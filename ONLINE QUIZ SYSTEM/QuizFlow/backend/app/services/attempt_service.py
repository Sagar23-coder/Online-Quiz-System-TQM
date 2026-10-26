"""
Quiz Attempt and Server-Side Scoring Service with Attempt Limits and Result Release Rules.
"""
from datetime import datetime, timedelta, timezone
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
    AttemptResultResponse,
    AttemptStartResponse,
    AttemptSummaryResponse,
    QuestionReviewItem,
)
from app.schemas.question import QuestionStudentResponse
from app.services.audit_service import AuditService


class AttemptService:
    @staticmethod
    def start_quiz(db: Session, quiz_id: int, student_id: int) -> AttemptStartResponse:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        if not quiz.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This quiz is not currently available.",
            )

        if quiz.is_disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This quiz has been disabled or closed by administrators.",
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

        # Check for active existing in-progress attempt
        existing_attempt = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
                QuizAttempt.status == AttemptStatus.IN_PROGRESS.value,
            )
            .first()
        )

        if existing_attempt:
            deadline = existing_attempt.deadline_time
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            if now > deadline + timedelta(seconds=15):
                AttemptService._grade_and_finalize(db, existing_attempt, status=AttemptStatus.EXPIRED.value)
            else:
                return AttemptService._build_start_response(db, existing_attempt, quiz, attempt_number=1)

        # Check maximum attempts restriction
        finished_attempts = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
                QuizAttempt.status != AttemptStatus.IN_PROGRESS.value,
            )
            .count()
        )
        if finished_attempts >= quiz.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have reached the maximum allowed attempts ({quiz.max_attempts}) for this quiz.",
            )

        # Create brand-new attempt
        start_time = now
        deadline_time = start_time + timedelta(minutes=quiz.duration_minutes)

        attempt = QuizAttempt(
            student_id=student_id,
            quiz_id=quiz.id,
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
            action="QUIZ_ATTEMPT_START",
            user_id=student_id,
            resource_type="attempt",
            resource_id=attempt.id,
            details={"quiz_id": quiz.id, "attempt_number": finished_attempts + 1},
        )

        return AttemptService._build_start_response(db, attempt, quiz, attempt_number=finished_attempts + 1)

    @staticmethod
    def save_answer(
        db: Session,
        attempt_id: int,
        student_id: int,
        ans_in: AnswerSubmitRequest,
    ) -> AnswerSubmitResponse:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        if attempt.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: You do not own this quiz attempt.",
            )

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
            AttemptService._grade_and_finalize(db, attempt, status=AttemptStatus.EXPIRED.value)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time expired! Quiz deadline has elapsed.",
            )

        question = (
            db.query(Question)
            .filter(Question.id == ans_in.question_id, Question.quiz_id == attempt.quiz_id)
            .first()
        )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid question for this quiz.",
            )

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
    def finish_quiz(db: Session, attempt_id: int, student_id: int) -> AttemptResultResponse:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        if attempt.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: You do not own this quiz attempt.",
            )

        if attempt.status != AttemptStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This quiz attempt has already been {attempt.status}.",
            )

        now = datetime.now(timezone.utc)
        deadline = attempt.deadline_time
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        final_status = (
            AttemptStatus.EXPIRED.value
            if now > deadline + timedelta(seconds=15)
            else AttemptStatus.COMPLETED.value
        )

        AttemptService._grade_and_finalize(db, attempt, status=final_status)

        AuditService.log(
            db,
            action="QUIZ_ATTEMPT_SUBMIT",
            user_id=student_id,
            resource_type="attempt",
            resource_id=attempt.id,
            details={"score": attempt.score_obtained, "percentage": attempt.percentage, "passed": attempt.is_passed},
        )

        return AttemptService.get_attempt_result(db, attempt.id, student_id=student_id)

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
    def get_attempt_result(
        db: Session,
        attempt_id: int,
        student_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> AttemptResultResponse:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        is_owner = (quiz and quiz.created_by_id == student_id) if student_id else False

        # If requesting user is neither admin, nor the student who took it, nor the organizer who owns the quiz:
        if not is_admin and not is_owner and student_id and attempt.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: You cannot access this attempt result.",
            )

        student = db.query(User).filter(User.id == attempt.student_id).first()
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

        # Check result release rules
        # If the requester is the student, and results are withheld by the organizer:
        results_released = quiz.results_released if quiz else True
        hide_solutions = (not is_admin and not is_owner and not results_released)

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

            if hide_solutions:
                # Do NOT reveal answer keys or explanations to student until organizer releases results
                review_items.append(
                    QuestionReviewItem(
                        question_id=q.id,
                        question_text=q.question_text,
                        option_a=q.option_a,
                        option_b=q.option_b,
                        option_c=q.option_c,
                        option_d=q.option_d,
                        selected_option=selected_option,
                        correct_option=None,  # Withheld
                        is_correct=False,      # Withheld
                        marks_awarded=0.0,     # Withheld
                        max_marks=q.marks,
                        explanation="Results and solutions have not yet been released by the organizer.",
                    )
                )
            else:
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

        score_to_show = 0.0 if hide_solutions else attempt.score_obtained
        pct_to_show = 0.0 if hide_solutions else attempt.percentage

        return AttemptResultResponse(
            attempt_id=attempt.id,
            quiz_id=attempt.quiz_id,
            quiz_title=quiz.title if quiz else "Quiz",
            student_name=student.full_name if student else "Student",
            status=attempt.status,
            start_time=attempt.start_time,
            end_time=attempt.end_time,
            deadline_time=attempt.deadline_time,
            score_obtained=score_to_show,
            total_marks=attempt.total_marks,
            percentage=pct_to_show,
            passing_percentage=quiz.passing_percentage if quiz else 50,
            is_passed=attempt.is_passed if not hide_solutions else False,
            total_questions=len(questions),
            correct_count=0 if hide_solutions else correct_count,
            incorrect_count=0 if hide_solutions else incorrect_count,
            unattempted_count=unattempted_count,
            results_released=results_released,
            review=review_items,
        )

    @staticmethod
    def get_student_history(db: Session, student_id: int) -> List[AttemptSummaryResponse]:
        attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.student_id == student_id)
            .order_by(QuizAttempt.created_at.desc())
            .all()
        )
        results = []
        for a in attempts:
            quiz = db.query(Quiz).filter(Quiz.id == a.quiz_id).first()
            is_rel = quiz.results_released if quiz else True
            results.append(
                AttemptSummaryResponse(
                    attempt_id=a.id,
                    quiz_id=a.quiz_id,
                    quiz_title=quiz.title if quiz else "Quiz",
                    status=a.status,
                    start_time=a.start_time,
                    end_time=a.end_time,
                    score_obtained=a.score_obtained if is_rel else 0.0,
                    total_marks=a.total_marks,
                    percentage=a.percentage if is_rel else 0.0,
                    is_passed=a.is_passed if is_rel else False,
                    results_released=is_rel,
                )
            )
        return results

    @staticmethod
    def get_student_dashboard_stats(db: Session, student_id: int) -> dict:
        attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.student_id == student_id)
            .order_by(QuizAttempt.created_at.desc())
            .all()
        )
        total_attempts = len(attempts)
        completed = [a for a in attempts if a.status in (AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value)]
        scores = [a.percentage for a in completed]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        passed_cnt = sum(1 for a in completed if a.is_passed)
        pass_rate = round((passed_cnt / len(completed)) * 100.0, 1) if completed else 0.0

        # Recent results
        recent_results = []
        for a in attempts[:6]:
            quiz = db.query(Quiz).filter(Quiz.id == a.quiz_id).first()
            is_rel = quiz.results_released if quiz else True
            recent_results.append({
                "attempt_id": a.id,
                "quiz_id": a.quiz_id,
                "quiz_title": quiz.title if quiz else "Quiz",
                "status": a.status,
                "score_obtained": a.score_obtained if is_rel else 0.0,
                "total_marks": a.total_marks,
                "percentage": a.percentage if is_rel else 0.0,
                "is_passed": a.is_passed if is_rel else False,
                "submitted_at": a.end_time.isoformat() if a.end_time else (a.created_at.isoformat() if a.created_at else None),
            })

        # Progress trend over recent attempts
        progress_trend = []
        if scores:
            for idx, s in enumerate(list(reversed(scores))[-6:]):
                progress_trend.append({"label": f"Wk {idx+1}", "score": s})
        else:
            progress_trend = [{"label": "Wk 1", "score": 0}]

        rank_text = "Top 10%" if avg_score >= 85 else "Top 20%" if avg_score >= 70 else "Top 35%" if avg_score >= 50 else "Active Learner"

        return {
            "total_attempts": total_attempts,
            "average_score": avg_score,
            "pass_rate": pass_rate,
            "rank_text": rank_text,
            "recent_results": recent_results,
            "progress_trend": progress_trend,
        }

    @staticmethod
    def _build_start_response(
        db: Session, attempt: QuizAttempt, quiz: Quiz, attempt_number: int = 1
    ) -> AttemptStartResponse:
        questions = (
            db.query(Question)
            .filter(Question.quiz_id == quiz.id)
            .order_by(Question.order_index.asc(), Question.id.asc())
            .all()
        )
        answers = db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == attempt.id).all()
        saved_answers: Dict[int, Optional[str]] = {a.question_id: a.selected_option for a in answers}

        student_questions = [
            QuestionStudentResponse(
                id=q.id,
                quiz_id=q.quiz_id,
                order_index=q.order_index,
                question_text=q.question_text,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
                marks=q.marks,
            )
            for q in questions
        ]

        return AttemptStartResponse(
            attempt_id=attempt.id,
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            duration_minutes=quiz.duration_minutes,
            start_time=attempt.start_time,
            deadline_time=attempt.deadline_time,
            questions=student_questions,
            saved_answers=saved_answers,
            max_attempts=quiz.max_attempts,
            attempt_number=attempt_number,
        )
