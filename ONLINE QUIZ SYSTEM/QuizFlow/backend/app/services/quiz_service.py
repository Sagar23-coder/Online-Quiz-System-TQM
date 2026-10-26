"""
Quiz and Question Management Service with Multi-Role Ownership and Join Codes.
Enforces strict creator ownership and administrator oversight.
"""
import csv
import io
import random
import string
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.attempt import AttemptStatus, QuizAttempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.question import QuestionAdminResponse, QuestionCreate, QuestionUpdate
from app.schemas.quiz import (
    OrganizerDashboardStats,
    ParticipantAttemptItem,
    QuestionPerformanceStat,
    QuizAdminResponse,
    QuizCreate,
    QuizReportResponse,
    QuizStudentResponse,
    QuizUpdate,
)
from app.services.audit_service import AuditService


def _generate_code() -> str:
    chars = "".join(c for c in string.ascii_uppercase + string.digits if c not in "IO01")
    return "QF-" + "".join(random.choices(chars, k=4))


class QuizService:
    @staticmethod
    def _get_unique_join_code(db: Session) -> str:
        for _ in range(10):
            code = _generate_code()
            if not db.query(Quiz).filter(Quiz.join_code == code).first():
                return code
        return "QF-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    @staticmethod
    def create_quiz(db: Session, quiz_in: QuizCreate, creator_id: int) -> QuizAdminResponse:
        join_code = QuizService._get_unique_join_code(db)
        quiz = Quiz(
            title=quiz_in.title.strip(),
            description=quiz_in.description.strip() if quiz_in.description else None,
            instructions=quiz_in.instructions.strip() if quiz_in.instructions else None,
            duration_minutes=quiz_in.duration_minutes,
            passing_percentage=quiz_in.passing_percentage,
            total_marks=0,
            is_published=False,
            is_public=quiz_in.is_public,
            max_attempts=quiz_in.max_attempts,
            release_results_immediately=quiz_in.release_results_immediately,
            results_released=quiz_in.release_results_immediately,
            start_time=quiz_in.start_time,
            end_time=quiz_in.end_time,
            is_disabled=False,
            join_code=join_code,
            created_by_id=creator_id,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        AuditService.log(
            db,
            action="QUIZ_CREATE",
            user_id=creator_id,
            resource_type="quiz",
            resource_id=quiz.id,
            details={"title": quiz.title, "join_code": quiz.join_code, "is_public": quiz.is_public},
        )

        creator = db.query(User).filter(User.id == creator_id).first()
        return QuizService._format_admin_quiz(quiz, question_count=0, creator_name=creator.full_name if creator else None)

    @staticmethod
    def update_quiz(
        db: Session,
        quiz_id: int,
        quiz_in: QuizUpdate,
        user_id: int,
        is_admin: bool = False,
    ) -> QuizAdminResponse:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        # Ownership authorization check
        if not is_admin and quiz.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify another organizer's quiz.",
            )

        if quiz_in.title is not None:
            quiz.title = quiz_in.title.strip()
        if quiz_in.description is not None:
            quiz.description = quiz_in.description.strip() if quiz_in.description else None
        if quiz_in.instructions is not None:
            quiz.instructions = quiz_in.instructions.strip() if quiz_in.instructions else None
        if quiz_in.duration_minutes is not None:
            quiz.duration_minutes = quiz_in.duration_minutes
        if quiz_in.passing_percentage is not None:
            quiz.passing_percentage = quiz_in.passing_percentage
        if quiz_in.is_public is not None:
            quiz.is_public = quiz_in.is_public
        if quiz_in.max_attempts is not None:
            quiz.max_attempts = quiz_in.max_attempts
        if quiz_in.release_results_immediately is not None:
            quiz.release_results_immediately = quiz_in.release_results_immediately
        if quiz_in.results_released is not None:
            quiz.results_released = quiz_in.results_released
        if quiz_in.start_time is not None:
            quiz.start_time = quiz_in.start_time
        if quiz_in.end_time is not None:
            quiz.end_time = quiz_in.end_time
        if quiz_in.is_published is not None:
            if quiz_in.is_published:
                QuizService._validate_for_publish(db, quiz)
            quiz.is_published = quiz_in.is_published

        db.commit()
        db.refresh(quiz)

        AuditService.log(
            db,
            action="QUIZ_UPDATE",
            user_id=user_id,
            resource_type="quiz",
            resource_id=quiz.id,
            details={"title": quiz.title, "is_published": quiz.is_published},
        )

        count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
        creator = db.query(User).filter(User.id == quiz.created_by_id).first()
        return QuizService._format_admin_quiz(quiz, question_count=count, creator_name=creator.full_name if creator else None)

    @staticmethod
    def delete_quiz(db: Session, quiz_id: int, user_id: int, is_admin: bool = False) -> bool:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        if not is_admin and quiz.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete another organizer's quiz.",
            )

        title = quiz.title
        db.delete(quiz)
        db.commit()

        AuditService.log(
            db,
            action="QUIZ_DELETE",
            user_id=user_id,
            resource_type="quiz",
            resource_id=quiz_id,
            details={"title": title},
        )
        return True

    @staticmethod
    def publish_quiz(db: Session, quiz_id: int, user_id: int, is_admin: bool = False) -> QuizAdminResponse:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        if not is_admin and quiz.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to publish another organizer's quiz.",
            )

        QuizService._validate_for_publish(db, quiz)
        quiz.is_published = True
        db.commit()
        db.refresh(quiz)

        AuditService.log(
            db,
            action="QUIZ_PUBLISH",
            user_id=user_id,
            resource_type="quiz",
            resource_id=quiz.id,
            details={"join_code": quiz.join_code},
        )

        count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
        creator = db.query(User).filter(User.id == quiz.created_by_id).first()
        return QuizService._format_admin_quiz(quiz, question_count=count, creator_name=creator.full_name if creator else None)

    @staticmethod
    def unpublish_quiz(db: Session, quiz_id: int, user_id: int, is_admin: bool = False) -> QuizAdminResponse:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        if not is_admin and quiz.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to unpublish another organizer's quiz.",
            )

        quiz.is_published = False
        db.commit()
        db.refresh(quiz)

        AuditService.log(
            db,
            action="QUIZ_UNPUBLISH",
            user_id=user_id,
            resource_type="quiz",
            resource_id=quiz.id,
        )

        count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
        creator = db.query(User).filter(User.id == quiz.created_by_id).first()
        return QuizService._format_admin_quiz(quiz, question_count=count, creator_name=creator.full_name if creator else None)

    @staticmethod
    def release_results(db: Session, quiz_id: int, user_id: int, is_admin: bool = False) -> QuizAdminResponse:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        if not is_admin and quiz.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to release results for this quiz.",
            )

        quiz.results_released = True
        db.commit()
        db.refresh(quiz)

        AuditService.log(
            db,
            action="QUIZ_RELEASE_RESULTS",
            user_id=user_id,
            resource_type="quiz",
            resource_id=quiz.id,
        )

        count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
        creator = db.query(User).filter(User.id == quiz.created_by_id).first()
        return QuizService._format_admin_quiz(quiz, question_count=count, creator_name=creator.full_name if creator else None)

    @staticmethod
    def _validate_for_publish(db: Session, quiz: Quiz) -> None:
        """Ensure quiz has at least one valid question and positive total marks."""
        questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a quiz with no questions. Please add questions first.",
            )

        total_marks = sum(q.marks for q in questions)
        if total_marks <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total marks for the quiz must be greater than zero.",
            )
        quiz.total_marks = total_marks

    # ------------------ Questions Management with Ownership ------------------
    @staticmethod
    def add_question(
        db: Session, quiz_id: int, q_in: QuestionCreate, user_id: int, is_admin: bool = False
    ) -> QuestionAdminResponse:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        if not is_admin and quiz.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to add questions to another organizer's quiz.",
            )

        max_order = (
            db.query(func.max(Question.order_index))
            .filter(Question.quiz_id == quiz_id)
            .scalar()
            or 0
        )
        order_index = q_in.order_index if q_in.order_index > 0 else max_order + 1

        question = Question(
            quiz_id=quiz_id,
            question_text=q_in.question_text.strip(),
            option_a=q_in.option_a.strip(),
            option_b=q_in.option_b.strip(),
            option_c=q_in.option_c.strip(),
            option_d=q_in.option_d.strip(),
            correct_option=q_in.correct_option.upper(),
            marks=q_in.marks,
            explanation=q_in.explanation.strip() if q_in.explanation else None,
            order_index=order_index,
        )
        db.add(question)
        db.flush()

        quiz.total_marks = (
            db.query(func.sum(Question.marks)).filter(Question.quiz_id == quiz_id).scalar() or 0
        )
        db.commit()
        db.refresh(question)
        return QuestionAdminResponse.model_validate(question)

    @staticmethod
    def update_question(
        db: Session, question_id: int, q_in: QuestionUpdate, user_id: int, is_admin: bool = False
    ) -> QuestionAdminResponse:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        quiz = db.query(Quiz).filter(Quiz.id == question.quiz_id).first()
        if not is_admin and quiz and quiz.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update questions in another organizer's quiz.",
            )

        if q_in.question_text is not None:
            question.question_text = q_in.question_text.strip()
        if q_in.option_a is not None:
            question.option_a = q_in.option_a.strip()
        if q_in.option_b is not None:
            question.option_b = q_in.option_b.strip()
        if q_in.option_c is not None:
            question.option_c = q_in.option_c.strip()
        if q_in.option_d is not None:
            question.option_d = q_in.option_d.strip()
        if q_in.correct_option is not None:
            question.correct_option = q_in.correct_option.upper()
        if q_in.marks is not None:
            question.marks = q_in.marks
        if q_in.explanation is not None:
            question.explanation = q_in.explanation.strip() if q_in.explanation else None
        if q_in.order_index is not None:
            question.order_index = q_in.order_index

        db.flush()
        if quiz:
            quiz.total_marks = (
                db.query(func.sum(Question.marks)).filter(Question.quiz_id == quiz.id).scalar() or 0
            )

        db.commit()
        db.refresh(question)
        return QuestionAdminResponse.model_validate(question)

    @staticmethod
    def delete_question(db: Session, question_id: int, user_id: int, is_admin: bool = False) -> bool:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        quiz_id = question.quiz_id
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not is_admin and quiz and quiz.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete questions from another organizer's quiz.",
            )

        db.delete(question)
        db.flush()

        if quiz:
            quiz.total_marks = (
                db.query(func.sum(Question.marks)).filter(Question.quiz_id == quiz_id).scalar() or 0
            )
            if quiz.total_marks == 0:
                quiz.is_published = False

        db.commit()
        return True

    # ------------------ Listings & Statistics ------------------
    @staticmethod
    def get_admin_quizzes(db: Session) -> List[QuizAdminResponse]:
        quizzes = db.query(Quiz).order_by(Quiz.created_at.desc()).all()
        results = []
        for q in quizzes:
            count = db.query(Question).filter(Question.quiz_id == q.id).count()
            attempts_cnt = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == q.id).count()
            creator = db.query(User).filter(User.id == q.created_by_id).first()
            results.append(
                QuizService._format_admin_quiz(
                    q,
                    question_count=count,
                    attempt_count=attempts_cnt,
                    creator_name=creator.full_name if creator else None,
                )
            )
        return results

    @staticmethod
    def get_organizer_quizzes(db: Session, organizer_id: int) -> List[QuizAdminResponse]:
        quizzes = db.query(Quiz).filter(Quiz.created_by_id == organizer_id).order_by(Quiz.created_at.desc()).all()
        results = []
        for q in quizzes:
            count = db.query(Question).filter(Question.quiz_id == q.id).count()
            attempts_cnt = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == q.id).count()
            results.append(
                QuizService._format_admin_quiz(
                    q,
                    question_count=count,
                    attempt_count=attempts_cnt,
                    creator_name="You",
                )
            )
        return results

    @staticmethod
    def get_organizer_dashboard_stats(db: Session, organizer_id: int) -> OrganizerDashboardStats:
        quizzes = db.query(Quiz).filter(Quiz.created_by_id == organizer_id).all()
        quiz_ids = [q.id for q in quizzes]

        total_quizzes = len(quizzes)
        published_quizzes = sum(1 for q in quizzes if q.is_published)
        draft_quizzes = total_quizzes - published_quizzes

        if not quiz_ids:
            return OrganizerDashboardStats(
                total_quizzes=0,
                published_quizzes=0,
                draft_quizzes=0,
                total_participants=0,
                total_attempts=0,
                average_score=0.0,
            )

        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id.in_(quiz_ids)).all()
        total_attempts = len(attempts)
        unique_participants = len({a.student_id for a in attempts})

        completed = [a.percentage for a in attempts if a.status in (AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value)]
        avg_score = round(sum(completed) / len(completed), 1) if completed else 0.0

        return OrganizerDashboardStats(
            total_quizzes=total_quizzes,
            published_quizzes=published_quizzes,
            draft_quizzes=draft_quizzes,
            total_participants=unique_participants,
            total_attempts=total_attempts,
            average_score=avg_score,
        )

    @staticmethod
    def get_student_quizzes(db: Session, student_id: Optional[int] = None) -> List[QuizStudentResponse]:
        """Return public published, non-disabled quizzes for participant browsing."""
        quizzes = (
            db.query(Quiz)
            .filter(Quiz.is_published == True, Quiz.is_public == True, Quiz.is_disabled == False)  # noqa: E712
            .order_by(Quiz.id.asc())
            .all()
        )
        results = []
        for q in quizzes:
            count = db.query(Question).filter(Question.quiz_id == q.id).count()
            if count > 0:
                attempts_taken = 0
                if student_id:
                    attempts_taken = db.query(QuizAttempt).filter(
                        QuizAttempt.quiz_id == q.id, QuizAttempt.student_id == student_id
                    ).count()

                creator = db.query(User).filter(User.id == q.created_by_id).first()
                results.append(
                    QuizStudentResponse(
                        id=q.id,
                        title=q.title,
                        description=q.description,
                        instructions=q.instructions,
                        duration_minutes=q.duration_minutes,
                        passing_percentage=q.passing_percentage,
                        total_marks=q.total_marks,
                        question_count=count,
                        join_code=q.join_code,
                        is_public=q.is_public,
                        creator_name=creator.full_name if creator else "Organizer",
                        max_attempts=q.max_attempts,
                        attempts_taken=attempts_taken,
                        results_released=q.results_released,
                    )
                )
        return results

    @staticmethod
    def get_quiz_by_join_code(db: Session, join_code: str, student_id: Optional[int] = None) -> QuizStudentResponse:
        """Find a quiz by its private or public join code and validate eligibility."""
        clean_code = join_code.strip().upper()
        quiz = db.query(Quiz).filter(Quiz.join_code == clean_code).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No quiz found matching this join code.")

        if not quiz.is_published:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This quiz is currently in draft mode and not available.")

        if quiz.is_disabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This quiz has been disabled or closed by platform administrators.")

        now = datetime.now(timezone.utc)
        if quiz.start_time and quiz.start_time.tzinfo is None:
            quiz.start_time = quiz.start_time.replace(tzinfo=timezone.utc)
        if quiz.end_time and quiz.end_time.tzinfo is None:
            quiz.end_time = quiz.end_time.replace(tzinfo=timezone.utc)

        if quiz.start_time and now < quiz.start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"This assessment opens at {quiz.start_time.strftime('%Y-%m-%d %H:%M UTC')}.")

        if quiz.end_time and now > quiz.end_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The deadline for this assessment has passed.")

        count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
        attempts_taken = 0
        if student_id:
            attempts_taken = db.query(QuizAttempt).filter(
                QuizAttempt.quiz_id == quiz.id, QuizAttempt.student_id == student_id
            ).count()

        creator = db.query(User).filter(User.id == quiz.created_by_id).first()
        return QuizStudentResponse(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            instructions=quiz.instructions,
            duration_minutes=quiz.duration_minutes,
            passing_percentage=quiz.passing_percentage,
            total_marks=quiz.total_marks,
            question_count=count,
            join_code=quiz.join_code,
            is_public=quiz.is_public,
            creator_name=creator.full_name if creator else "Organizer",
            max_attempts=quiz.max_attempts,
            attempts_taken=attempts_taken,
            results_released=quiz.results_released,
        )

    @staticmethod
    def get_quiz_report(db: Session, quiz_id: int, user_id: int, is_admin: bool = False) -> QuizReportResponse:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        if not is_admin and quiz.created_by_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to another organizer's reports.")

        attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.created_at.desc())
            .all()
        )

        attempt_items = []
        for a in attempts:
            st = db.query(User).filter(User.id == a.student_id).first()
            attempt_items.append(
                ParticipantAttemptItem(
                    attempt_id=a.id,
                    student_id=a.student_id,
                    student_name=st.full_name if st else "Unknown",
                    student_email=st.email if st else "N/A",
                    status=a.status,
                    score_obtained=a.score_obtained,
                    total_marks=a.total_marks,
                    percentage=a.percentage,
                    is_passed=a.is_passed,
                    submitted_at=a.end_time or a.created_at,
                )
            )

        completed_attempts = [a for a in attempts if a.status in (AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value)]
        scores = [a.percentage for a in completed_attempts]

        total_attempts = len(attempts)
        unique_participants = len({a.student_id for a in attempts})
        pass_count = sum(1 for a in completed_attempts if a.is_passed)
        fail_count = len(completed_attempts) - pass_count

        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        hi_score = max(scores) if scores else 0.0
        lo_score = min(scores) if scores else 0.0
        pass_pct = round((pass_count / len(completed_attempts)) * 100, 1) if completed_attempts else 0.0

        # Question statistics with Distractor & Misconception Analysis
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).order_by(Question.order_index.asc()).all()
        q_stats = []
        topic_aggregates: Dict[str, Dict[str, Any]] = {}
        misconceptions_list = []

        for q in questions:
            answers = db.query(AttemptAnswer).filter(AttemptAnswer.question_id == q.id).all()
            tot_ans = len(answers)
            correct_ans = sum(1 for ans in answers if ans.is_correct)
            acc_pct = round((correct_ans / tot_ans) * 100, 1) if tot_ans > 0 else 0.0

            # Distractor frequency analysis
            wrong_option_counts: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
            for ans in answers:
                if not ans.is_correct and ans.selected_option in wrong_option_counts:
                    wrong_option_counts[ans.selected_option] += 1

            common_wrong_opt = None
            common_wrong_cnt = 0
            common_wrong_pct = 0.0
            misconception_note = None

            if tot_ans > 0:
                # Find the most chosen wrong option
                sorted_wrongs = sorted(wrong_option_counts.items(), key=lambda x: x[1], reverse=True)
                if sorted_wrongs and sorted_wrongs[0][1] > 0:
                    common_wrong_opt, common_wrong_cnt = sorted_wrongs[0]
                    common_wrong_pct = round((common_wrong_cnt / tot_ans) * 100, 1)

                    if common_wrong_pct >= 25.0 and acc_pct < 70.0:
                        misconception_note = (
                            f"Identified distractor pattern: {common_wrong_pct}% of students selected Option {common_wrong_opt} "
                            f"instead of correct Option {q.correct_option}. Indicates conceptual confusion on {q.topic or 'this concept'}."
                        )
                        misconceptions_list.append({
                            "question_id": q.id,
                            "question_text": q.question_text,
                            "topic": q.topic or "General",
                            "correct_option": q.correct_option,
                            "common_distractor": common_wrong_opt,
                            "distractor_percentage": common_wrong_pct,
                            "accuracy_percentage": acc_pct,
                            "explanation": q.explanation or "Review core definition and contrast with distractor option.",
                            "recommended_action": f"Review {q.topic or 'this concept'} specifically clarifying why Option {common_wrong_opt} is incorrect."
                        })

            q_topic = q.topic or "General"
            if q_topic not in topic_aggregates:
                topic_aggregates[q_topic] = {"total_questions": 0, "total_answers": 0, "correct_answers": 0}
            topic_aggregates[q_topic]["total_questions"] += 1
            topic_aggregates[q_topic]["total_answers"] += tot_ans
            topic_aggregates[q_topic]["correct_answers"] += correct_ans

            q_stats.append(
                QuestionPerformanceStat(
                    question_id=q.id,
                    question_text=q.question_text,
                    total_answers=tot_ans,
                    correct_answers=correct_ans,
                    accuracy_percentage=acc_pct,
                    topic=q.topic or "General",
                    difficulty=q.difficulty or "medium",
                    common_wrong_option=common_wrong_opt,
                    common_wrong_count=common_wrong_cnt,
                    common_wrong_percentage=common_wrong_pct,
                    misconception_note=misconception_note,
                )
            )

        # Build Topic Breakdown
        topic_breakdown = []
        for t_name, t_data in topic_aggregates.items():
            t_acc = round((t_data["correct_answers"] / t_data["total_answers"]) * 100, 1) if t_data["total_answers"] > 0 else 0.0
            if t_acc < 50.0:
                t_status = "🚨 Critical Misconception / High Need"
            elif t_acc < 75.0:
                t_status = "⚠️ Needs Practice / Review"
            else:
                t_status = "✅ Concept Mastered"

            topic_breakdown.append({
                "topic": t_name,
                "question_count": t_data["total_questions"],
                "total_answers": t_data["total_answers"],
                "accuracy_percentage": t_acc,
                "status": t_status,
            })

        # Teacher Action Center Recommendations
        recommended_actions = []
        # Action for low accuracy topics
        for tb in topic_breakdown:
            if tb["accuracy_percentage"] < 65.0 and tb["total_answers"] > 0:
                recommended_actions.append({
                    "priority": "HIGH",
                    "category": "Topic Revision",
                    "title": f"Schedule Revision: {tb['topic']}",
                    "description": f"Class accuracy on {tb['topic']} is {tb['accuracy_percentage']}%. Recommend a 10-minute targeted review before next exam.",
                    "action_type": "revision_review",
                    "topic": tb["topic"],
                })

        # Action for struggling participants
        struggling_students = [a for a in attempt_items if not a.is_passed and a.status in (AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value)]
        if struggling_students:
            names = ", ".join({s.student_name for s in struggling_students[:3]})
            recommended_actions.append({
                "priority": "MEDIUM",
                "category": "Student Support",
                "title": f"Follow-up with {len(struggling_students)} Struggling Student(s)",
                "description": f"Students needing additional support: {names}. Consider offering practice attempt or 1-on-1 feedback.",
                "action_type": "student_outreach",
                "count": len(struggling_students),
            })

        # Action for distractor misconceptions
        if misconceptions_list:
            recommended_actions.append({
                "priority": "HIGH",
                "category": "Misconception Alert",
                "title": f"Clarify {len(misconceptions_list)} Common Exam Distractor(s)",
                "description": f"Significant clustering on wrong answer options detected in {len(misconceptions_list)} question(s). Open Misconception Detector tab to inspect details.",
                "action_type": "distractor_clarification",
                "count": len(misconceptions_list),
            })

        if not recommended_actions and total_attempts > 0:
            recommended_actions.append({
                "priority": "INFO",
                "category": "Class Achievement",
                "title": "High Overall Mastery Achieved",
                "description": f"The class achieved an average score of {avg_score}%. Core objectives are well understood.",
                "action_type": "celebrate",
            })

        return QuizReportResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            subject=quiz.subject or "General",
            join_code=quiz.join_code,
            is_published=quiz.is_published,
            results_released=quiz.results_released,
            total_marks=quiz.total_marks,
            passing_percentage=quiz.passing_percentage,
            total_attempts=total_attempts,
            unique_participants=unique_participants,
            average_score=avg_score,
            highest_score=hi_score,
            lowest_score=lo_score,
            pass_count=pass_count,
            fail_count=fail_count,
            pass_percentage=pass_pct,
            attempts=attempt_items,
            question_stats=q_stats,
            misconceptions=misconceptions_list,
            topic_breakdown=topic_breakdown,
            recommended_actions=recommended_actions,
        )

    @staticmethod
    def export_quiz_csv(db: Session, quiz_id: int, user_id: int, is_admin: bool = False) -> str:
        report = QuizService.get_quiz_report(db, quiz_id, user_id, is_admin)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Attempt ID",
            "Student Name",
            "Student Email",
            "Score Obtained",
            "Total Marks",
            "Percentage",
            "Passed",
            "Status",
            "Submitted Date (UTC)",
        ])

        for a in report.attempts:
            writer.writerow([
                a.attempt_id,
                a.student_name,
                a.student_email,
                a.score_obtained,
                a.total_marks,
                f"{a.percentage}%",
                "YES" if a.is_passed else "NO",
                a.status,
                a.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if a.submitted_at else "In Progress",
            ])

        return output.getvalue()

    @staticmethod
    def get_quiz_questions_admin(db: Session, quiz_id: int) -> List[QuestionAdminResponse]:
        questions = (
            db.query(Question)
            .filter(Question.quiz_id == quiz_id)
            .order_by(Question.order_index.asc(), Question.id.asc())
            .all()
        )
        return [QuestionAdminResponse.model_validate(q) for q in questions]

    @staticmethod
    def _format_admin_quiz(
        quiz: Quiz,
        question_count: int,
        attempt_count: int = 0,
        creator_name: Optional[str] = None,
    ) -> QuizAdminResponse:
        return QuizAdminResponse(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            instructions=quiz.instructions,
            duration_minutes=quiz.duration_minutes,
            passing_percentage=quiz.passing_percentage,
            total_marks=quiz.total_marks,
            is_published=quiz.is_published,
            join_code=quiz.join_code,
            is_public=quiz.is_public,
            max_attempts=quiz.max_attempts,
            release_results_immediately=quiz.release_results_immediately,
            results_released=quiz.results_released,
            start_time=quiz.start_time,
            end_time=quiz.end_time,
            is_disabled=quiz.is_disabled,
            created_by_id=quiz.created_by_id,
            creator_name=creator_name,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
            question_count=question_count,
            attempt_count=attempt_count,
        )
