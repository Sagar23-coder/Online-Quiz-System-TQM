"""
Public Quiz API Endpoints for Students (No Login Required).
Enables seamless assessment access through secure share links.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.attempt import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    IntegrityEventRequest,
    PracticeCheckRequest,
    PracticeCheckResponse,
    PublicAttemptResultResponse,
    PublicAttemptStartResponse,
    PublicQuizInfoResponse,
    PublicStudentDetailsRequest,
    SubmitAttemptRequest,
)
from app.services.public_quiz_service import PublicQuizService

router = APIRouter()


@router.get(
    "/quiz/{share_token}",
    response_model=PublicQuizInfoResponse,
    summary="Get public quiz overview and instructions",
)
def get_public_quiz_info(
    share_token: str,
    db: Session = Depends(get_db),
):
    """
    Returns public quiz metadata prior to starting.
    Strictly withholds questions and answers to maintain assessment integrity.
    """
    return PublicQuizService.get_public_quiz_info(db, share_token=share_token)


@router.post(
    "/quiz/{share_token}/start",
    response_model=PublicAttemptStartResponse,
    summary="Start student quiz attempt from public link",
)
def start_public_quiz(
    share_token: str,
    details: PublicStudentDetailsRequest,
    db: Session = Depends(get_db),
):
    """
    Validates student information, enforces duplicate attempt rules,
    initializes the server-side countdown timer, and returns safe question cards.
    """
    return PublicQuizService.start_public_attempt(db, share_token=share_token, details=details)


@router.post(
    "/attempt/{attempt_token}/save",
    response_model=AnswerSubmitResponse,
    summary="Save answer selection for in-progress public attempt",
)
def save_public_answer(
    attempt_token: str,
    ans_in: AnswerSubmitRequest,
    db: Session = Depends(get_db),
):
    """
    Saves or clears an answer choice while the attempt is actively in progress.
    """
    return PublicQuizService.save_public_answer(db, attempt_token=attempt_token, ans_in=ans_in)


@router.post(
    "/attempt/{attempt_token}/submit",
    response_model=PublicAttemptResultResponse,
    summary="Submit and evaluate public quiz attempt",
)
def submit_public_attempt(
    attempt_token: str,
    req: Optional[SubmitAttemptRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Finalizes the student attempt, performs server-authoritative grading,
    persists result metrics, and returns the instant score report.
    """
    return PublicQuizService.submit_public_attempt(db, attempt_token=attempt_token, req=req)


@router.get(
    "/attempt/{attempt_token}/result",
    response_model=PublicAttemptResultResponse,
    summary="Retrieve score report for submitted public attempt",
)
def get_public_result(
    attempt_token: str,
    db: Session = Depends(get_db),
):
    """
    Returns the student scorecard and question review items (if released).
    """
    return PublicQuizService.get_public_result(db, attempt_token=attempt_token)


@router.post(
    "/attempt/{attempt_token}/check-answer",
    response_model=PracticeCheckResponse,
    summary="Practice Mode: Check answer selection and receive immediate feedback",
)
def check_practice_answer(
    attempt_token: str,
    req: PracticeCheckRequest,
    db: Session = Depends(get_db),
):
    """
    Returns immediate formative explanation and correctness for Practice Mode assessments.
    """
    return PublicQuizService.check_practice_answer(db, attempt_token=attempt_token, req=req)


@router.post(
    "/attempt/{attempt_token}/integrity-event",
    summary="Secure Exam Mode: Log student client integrity event",
)
def log_integrity_event(
    attempt_token: str,
    req: IntegrityEventRequest,
    db: Session = Depends(get_db),
):
    """
    Records student tab switches, window blur events, and network transitions.
    """
    return PublicQuizService.log_integrity_event(db, attempt_token=attempt_token, req=req)
