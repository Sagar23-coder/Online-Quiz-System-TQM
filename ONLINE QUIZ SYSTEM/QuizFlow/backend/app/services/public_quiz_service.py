"""
Public Quiz Service for Link-Based Student Participation.
Enables students to participate in quizzes without accounts or login:
- Secure unguessable token validation
- Public metadata disclosure (questions hidden prior to starting)
- Contact normalization and duplicate attempt enforcement
- Server-authoritative timer and instant result grading
"""
from datetime import datetime, timedelta, timezone
import re
import secrets
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.attempt import AttemptStatus, QuizAttempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.attempt import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    PublicAttemptResultResponse,
    PublicAttemptStartResponse,
    PublicQuizInfoResponse,
    PublicStudentDetailsRequest,
    QuestionReviewItem,
)
from app.schemas.question import QuestionStudentResponse
from app.services.audit_service import AuditService


class PublicQuizService:
    @staticmethod
    def _normalize_email(email: Optional[str]) -> Optional[str]:
        if not email:
            return None
        clean = email.strip().lower()
        return clean if clean else None

    @staticmethod
    def _normalize_phone(phone: Optional[str]) -> Optional[str]:
        if not phone:
            return None
        # Remove whitespace, dashes, parens, dots, etc.
        clean = re.sub(r"[\s\-\(\)\.]", "", phone.strip())
        return clean if clean else None

    @staticmethod
    def _validate_student_details(req: PublicStudentDetailsRequest) -> tuple[str, str, str, Optional[str], Optional[str]]:
        name = req.full_name.strip()
        s_class = req.student_class.strip()
        section = req.section.strip()
        email = PublicQuizService._normalize_email(req.email)
        phone = PublicQuizService._normalize_phone(req.phone)

        if len(name) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Full name is required and must be at least 2 characters.",
            )

        if not s_class:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Class / Grade is required.",
            )

        if not section:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Section is required.",
            )

        if not email and not phone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one contact method (Email Address or Mobile Number) is required.",
            )

        if email:
            email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
            if not re.match(email_regex, email):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Please enter a valid email address.",
                )

        if phone:
            phone_regex = r"^\+?[0-9]{7,15}$"
            if not re.match(phone_regex, phone):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Please enter a valid phone number with digits (and optional leading +).",
                )

        return name, s_class, section, email, phone

    @staticmethod
    def get_public_quiz_info(db: Session, share_token: str) -> PublicQuizInfoResponse:
        quiz = db.query(Quiz).filter(Quiz.share_token == share_token).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found. Please check your link.")

        if not quiz.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This assessment is currently in draft mode and has not yet been published by the instructor.",
            )

        if not getattr(quiz, "is_share_link_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This quiz link has been deactivated by the instructor.",
            )

        if quiz.is_disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This assessment is temporarily disabled by administrators.",
            )

        now = datetime.now(timezone.utc)
        if quiz.start_time:
            st = quiz.start_time.replace(tzinfo=timezone.utc) if quiz.start_time.tzinfo is None else quiz.start_time
            if now < st:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This assessment does not open until {st.strftime('%Y-%m-%d %H:%M UTC')}.",
                )

        if quiz.end_time:
            et = quiz.end_time.replace(tzinfo=timezone.utc) if quiz.end_time.tzinfo is None else quiz.end_time
            if now > et:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The closing deadline for this assessment has passed.",
                )

        total_questions = db.query(Question).filter(Question.quiz_id == quiz.id).count()
        teacher = db.query(User).filter(User.id == quiz.created_by_id).first()

        return PublicQuizInfoResponse(
            title=quiz.title,
            subject=quiz.subject or "General",
            description=quiz.description,
            instructions=quiz.instructions,
            teacher_name=teacher.full_name if teacher else "Instructor",
            duration_minutes=quiz.duration_minutes,
            total_questions=total_questions,
            total_marks=quiz.total_marks,
            passing_percentage=quiz.passing_percentage,
            is_published=quiz.is_published,
            is_active=quiz.is_share_link_active,
            max_attempts=quiz.max_attempts,
        )

    @staticmethod
    def start_public_attempt(
        db: Session, share_token: str, details: PublicStudentDetailsRequest
    ) -> PublicAttemptStartResponse:
        name, s_class, section, email, phone = PublicQuizService._validate_student_details(details)

        quiz = db.query(Quiz).filter(Quiz.share_token == share_token).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

        if not quiz.is_published or not getattr(quiz, "is_share_link_active", True) or quiz.is_disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This assessment is not currently accepting submissions.",
            )

        now = datetime.now(timezone.utc)
        if quiz.start_time:
            st = quiz.start_time.replace(tzinfo=timezone.utc) if quiz.start_time.tzinfo is None else quiz.start_time
            if now < st:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This assessment does not open until {st.strftime('%Y-%m-%d %H:%M UTC')}.",
                )

        if quiz.end_time:
            et = quiz.end_time.replace(tzinfo=timezone.utc) if quiz.end_time.tzinfo is None else quiz.end_time
            if now > et:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The closing deadline for this assessment has passed.",
                )

        # ------------------ Duplicate Attempt Check ------------------
        # Find finished attempts matching either normalized email or phone
        dup_query = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == quiz.id,
            QuizAttempt.status != AttemptStatus.IN_PROGRESS.value,
        )
        if email and phone:
            dup_query = dup_query.filter(
                (QuizAttempt.participant_email == email) | (QuizAttempt.participant_phone == phone)
            )
        elif email:
            dup_query = dup_query.filter(QuizAttempt.participant_email == email)
        else:
            dup_query = dup_query.filter(QuizAttempt.participant_phone == phone)

        finished_count = dup_query.count()
        if finished_count >= quiz.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already completed the maximum allowed attempts ({quiz.max_attempts}) for this quiz.",
            )

        # Check for active existing in-progress attempt for this participant
        active_query = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == quiz.id,
            QuizAttempt.status == AttemptStatus.IN_PROGRESS.value,
        )
        if email and phone:
            active_query = active_query.filter(
                (QuizAttempt.participant_email == email) | (QuizAttempt.participant_phone == phone)
            )
        elif email:
            active_query = active_query.filter(QuizAttempt.participant_email == email)
        else:
            active_query = active_query.filter(QuizAttempt.participant_phone == phone)

        existing_attempt = active_query.first()
        if existing_attempt:
            deadline = existing_attempt.deadline_time
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            if now > deadline + timedelta(seconds=15):
                # Expired in-progress attempt
                PublicQuizService._grade_and_finalize(db, existing_attempt, status=AttemptStatus.EXPIRED.value)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Your previous attempt time expired.",
                )
            else:
                # Resume in-progress attempt (e.g. accidental browser refresh)
                return PublicQuizService._build_start_response(db, existing_attempt, quiz)

        # Create brand-new attempt
        start_time = now
        deadline_time = start_time + timedelta(minutes=quiz.duration_minutes)
        attempt_token = secrets.token_urlsafe(24)

        attempt = QuizAttempt(
            student_id=None,
            quiz_id=quiz.id,
            participant_name=name,
            participant_class=s_class,
            participant_section=section,
            participant_email=email,
            participant_phone=phone,
            attempt_token=attempt_token,
            start_time=start_time,
            deadline_time=deadline_time,
            status=AttemptStatus.IN_PROGRESS.value,
            total_marks=float(quiz.total_marks),
            score_obtained=0.0,
            percentage=0.0,
            is_passed=False,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        AuditService.log(
            db,
            action="PUBLIC_QUIZ_ATTEMPT_START",
            user_id=None,
            resource_type="attempt",
            resource_id=attempt.id,
            details={
                "quiz_id": quiz.id,
                "participant_name": name,
                "class": s_class,
                "section": section,
            },
        )

        return PublicQuizService._build_start_response(db, attempt, quiz)

    @staticmethod
    def _build_start_response(db: Session, attempt: QuizAttempt, quiz: Quiz) -> PublicAttemptStartResponse:
        questions = (
            db.query(Question)
            .filter(Question.quiz_id == quiz.id)
            .order_by(Question.order_index.asc(), Question.id.asc())
            .all()
        )

        saved_answers = {
            a.question_id: a.selected_option
            for a in db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == attempt.id).all()
        }

        now = datetime.now(timezone.utc)
        deadline = attempt.deadline_time
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        remaining = max(0, int((deadline - now).total_seconds()))

        # Sanitize questions (never leak correct_option or explanation to student!)
        safe_questions = [
            QuestionStudentResponse(
                id=q.id,
                quiz_id=q.quiz_id,
                question_text=q.question_text,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
                marks=q.marks,
                order_index=q.order_index,
            )
            for q in questions
        ]

        return PublicAttemptStartResponse(
            attempt_token=attempt.attempt_token,
            quiz_title=quiz.title,
            student_name=attempt.participant_name or "Student",
            student_class=attempt.participant_class or "",
            student_section=attempt.participant_section or "",
            duration_minutes=quiz.duration_minutes,
            start_time=attempt.start_time,
            deadline_time=attempt.deadline_time,
            remaining_seconds=remaining,
            questions=safe_questions,
            saved_answers=saved_answers,
        )

    @staticmethod
    def save_public_answer(
        db: Session, attempt_token: str, ans_in: AnswerSubmitRequest
    ) -> AnswerSubmitResponse:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.attempt_token == attempt_token).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

        if attempt.status != AttemptStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot save answer: attempt is already {attempt.status}.",
            )

        now = datetime.now(timezone.utc)
        deadline = attempt.deadline_time
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if now > deadline + timedelta(seconds=15):
            PublicQuizService._grade_and_finalize(db, attempt, status=AttemptStatus.EXPIRED.value)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment time expired. Attempt auto-submitted.",
            )

        question = (
            db.query(Question)
            .filter(Question.id == ans_in.question_id, Question.quiz_id == attempt.quiz_id)
            .first()
        )
        if not question:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question.")

        existing_answer = (
            db.query(AttemptAnswer)
            .filter(
                AttemptAnswer.attempt_id == attempt.id,
                AttemptAnswer.question_id == question.id,
            )
            .first()
        )

        if existing_answer:
            existing_answer.selected_option = ans_in.selected_option
            existing_answer.answered_at = now
        else:
            new_answer = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option=ans_in.selected_option,
                answered_at=now,
            )
            db.add(new_answer)

        db.commit()
        return AnswerSubmitResponse(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option=ans_in.selected_option,
            saved=True,
        )

    @staticmethod
    def submit_public_attempt(db: Session, attempt_token: str) -> PublicAttemptResultResponse:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.attempt_token == attempt_token).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

        if attempt.status != AttemptStatus.IN_PROGRESS.value:
            # Already submitted or finalized: return existing result
            return PublicQuizService.get_public_result(db, attempt_token)

        now = datetime.now(timezone.utc)
        deadline = attempt.deadline_time
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        final_status = (
            AttemptStatus.EXPIRED.value
            if now > deadline + timedelta(seconds=15)
            else AttemptStatus.COMPLETED.value
        )

        PublicQuizService._grade_and_finalize(db, attempt, status=final_status)

        AuditService.log(
            db,
            action="PUBLIC_QUIZ_ATTEMPT_SUBMIT",
            user_id=None,
            resource_type="attempt",
            resource_id=attempt.id,
            details={
                "participant_name": attempt.participant_name,
                "score": attempt.score_obtained,
                "percentage": attempt.percentage,
                "is_passed": attempt.is_passed,
            },
        )

        return PublicQuizService.get_public_result(db, attempt_token)

    @staticmethod
    def _grade_and_finalize(db: Session, attempt: QuizAttempt, status: str) -> None:
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        questions = db.query(Question).filter(Question.quiz_id == attempt.quiz_id).all()

        answers_map = {
            a.question_id: a
            for a in db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == attempt.id).all()
        }

        total_score = 0.0
        total_quiz_marks = sum(q.marks for q in questions) if questions else 0.0

        for q in questions:
            ans = answers_map.get(q.id)
            if ans and ans.selected_option and ans.selected_option.upper() == q.correct_option.upper():
                ans.is_correct = True
                ans.marks_awarded = float(q.marks)
                total_score += float(q.marks)
            else:
                if ans:
                    ans.is_correct = False
                    ans.marks_awarded = 0.0

        attempt.score_obtained = total_score
        attempt.total_marks = float(total_quiz_marks)
        if total_quiz_marks > 0:
            attempt.percentage = round((total_score / total_quiz_marks) * 100.0, 2)
        else:
            attempt.percentage = 0.0

        passing_percentage = quiz.passing_percentage if quiz else 50
        attempt.is_passed = attempt.percentage >= passing_percentage
        attempt.status = status
        attempt.end_time = datetime.now(timezone.utc)

        db.commit()
        db.refresh(attempt)

    @staticmethod
    def get_public_result(db: Session, attempt_token: str) -> PublicAttemptResultResponse:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.attempt_token == attempt_token).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        questions = (
            db.query(Question)
            .filter(Question.quiz_id == attempt.quiz_id)
            .order_by(Question.order_index.asc(), Question.id.asc())
            .all()
        )

        answers_map = {
            a.question_id: a
            for a in db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == attempt.id).all()
        }

        # Release review items if permitted by quiz settings
        results_released = (quiz.results_released or quiz.release_results_immediately) if quiz else True

        correct_count = 0
        incorrect_count = 0
        unattempted_count = 0
        review_items: List[QuestionReviewItem] = []

        for q in questions:
            ans = answers_map.get(q.id)
            selected_option = ans.selected_option if ans else None
            is_correct = ans.is_correct if ans else False
            marks_awarded = ans.marks_awarded if ans else 0.0

            if selected_option is None:
                unattempted_count += 1
            elif is_correct:
                correct_count += 1
            else:
                incorrect_count += 1

            if results_released:
                review_items.append(
                    QuestionReviewItem(
                        question_id=q.id,
                        question_text=q.question_text,
                        option_a=q.option_a,
                        option_b=q.option_b,
                        option_c=q.option_c,
                        option_d=q.option_d,
                        selected_option=selected_option,
                        correct_option=q.correct_option,
                        is_correct=is_correct,
                        marks_awarded=marks_awarded,
                        max_marks=q.marks,
                        explanation=q.explanation,
                    )
                )

        return PublicAttemptResultResponse(
            attempt_token=attempt.attempt_token,
            quiz_title=quiz.title if quiz else "Quiz Assessment",
            student_name=attempt.participant_name or "Student",
            student_class=attempt.participant_class,
            student_section=attempt.participant_section,
            score_obtained=attempt.score_obtained,
            total_marks=attempt.total_marks,
            percentage=attempt.percentage,
            passing_percentage=quiz.passing_percentage if quiz else 50,
            is_passed=attempt.is_passed,
            total_questions=len(questions),
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unattempted_count=unattempted_count,
            submitted_at=attempt.end_time or attempt.start_time,
            results_released=results_released,
            review=review_items if results_released else None,
        )
