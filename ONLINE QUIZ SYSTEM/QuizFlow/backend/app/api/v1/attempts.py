"""
Quiz Attempt, Answer Submission, and Scoring Endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_student, get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.attempt import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    AttemptResultResponse,
    AttemptStartResponse,
    AttemptSummaryResponse,
    StudentDashboardStatsResponse,
)
from app.services.attempt_service import AttemptService

router = APIRouter()


@router.post(
    "/quizzes/{quiz_id}/start",
    response_model=AttemptStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or resume a quiz attempt (Student)",
)
def start_quiz_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    """
    Initiates an attempt, computes deadline timestamp on the server,
    and returns questions without leaking correct answers.
    """
    return AttemptService.start_quiz(db, quiz_id, current_student.id)


@router.post(
    "/{attempt_id}/answers",
    response_model=AnswerSubmitResponse,
    summary="Record or update an answer for a question",
)
def save_answer(
    attempt_id: int,
    ans_in: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    """
    Saves an option selection for a question while the attempt timer is active.
    """
    return AttemptService.save_answer(db, attempt_id, current_student.id, ans_in)


@router.post(
    "/{attempt_id}/finish",
    response_model=AttemptResultResponse,
    summary="Finish and submit quiz attempt for server grading",
)
def finish_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    """
    Calculates final score on the server, evaluates pass/fail, and finalizes the attempt.
    """
    return AttemptService.finish_quiz(db, attempt_id, current_student.id)


@router.get(
    "/{attempt_id}/result",
    response_model=AttemptResultResponse,
    summary="Get result breakdown for a completed attempt",
)
def get_attempt_result(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns results and question reviews with correct options and explanations.
    """
    is_admin = current_user.role == UserRole.ADMIN.value
    return AttemptService.get_attempt_result(
        db,
        attempt_id,
        student_id=current_user.id,
        is_admin=is_admin,
    )


@router.get(
    "/my-history",
    response_model=List[AttemptSummaryResponse],
    summary="Get current student's quiz attempt history",
)
def get_my_history(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    """
    Returns summary of all past attempts for the logged-in student.
    """
    return AttemptService.get_student_history(db, current_student.id)


@router.get(
    "/my-dashboard-stats",
    response_model=StudentDashboardStatsResponse,
    summary="Get summarized statistics and progress for student dashboard",
)
def get_student_dashboard_stats(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    """
    Returns attempts, average score, pass rate, rank, recent results, and weekly trend.
    """
    return AttemptService.get_student_dashboard_stats(db, current_student.id)
