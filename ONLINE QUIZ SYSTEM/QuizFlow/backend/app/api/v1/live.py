"""
Live Assessment Endpoints for QuizFlow 2.0.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_db
from app.models.user import User
from app.services.live_quiz_service import LiveQuizService

router = APIRouter()


class LiveCreateRequest(BaseModel):
    quiz_id: int
    mode: str = "instructor_paced"


class LiveJoinRequest(BaseModel):
    pin: str
    nickname: str


class LiveAnswerRequest(BaseModel):
    participant_token: str
    question_id: int
    selected_option: str
    time_spent_sec: float = Field(5.0, ge=0.1, le=120.0)


@router.post("/create", summary="Teacher: Create a synchronized live assessment session")
def create_live_session(
    req: LiveCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return LiveQuizService.create_session(db, teacher_id=current_user.id, quiz_id=req.quiz_id, mode=req.mode)


@router.post("/join", summary="Student: Join a live assessment with PIN & nickname")
def join_live_session(
    req: LiveJoinRequest,
    db: Session = Depends(get_db),
):
    return LiveQuizService.join_session(db, pin=req.pin, nickname=req.nickname)


@router.get("/{session_pin}/state", summary="Polling: Get real-time session state, active question & leaderboard")
def get_live_state(
    session_pin: str,
    token: Optional[str] = Query(None, description="Participant token"),
    db: Session = Depends(get_db),
):
    return LiveQuizService.get_session_state(db, pin=session_pin, participant_token=token)


@router.post("/{session_pin}/start", summary="Teacher: Start live session from lobby")
def start_live_session(
    session_pin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return LiveQuizService.start_session(db, pin=session_pin, teacher_id=current_user.id)


@router.post("/{session_pin}/next", summary="Teacher: Advance to the next question")
def next_live_question(
    session_pin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return LiveQuizService.next_question(db, pin=session_pin, teacher_id=current_user.id)


@router.post("/{session_pin}/answer", summary="Student: Submit live question answer with speed bonus")
def submit_live_answer(
    session_pin: str,
    req: LiveAnswerRequest,
    db: Session = Depends(get_db),
):
    return LiveQuizService.submit_answer(
        db,
        pin=session_pin,
        participant_token=req.participant_token,
        question_id=req.question_id,
        selected_option=req.selected_option,
        time_spent_sec=req.time_spent_sec,
    )


@router.post("/{session_pin}/end", summary="Teacher: Conclude live assessment session and reveal final podium")
def end_live_session(
    session_pin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return LiveQuizService.end_session(db, pin=session_pin, teacher_id=current_user.id)
