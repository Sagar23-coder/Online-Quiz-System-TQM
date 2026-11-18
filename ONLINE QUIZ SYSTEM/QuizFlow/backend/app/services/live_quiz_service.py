"""
Live Assessment Service for QuizFlow 2.0.
Synchronized classroom exam sessions with 6-digit PIN join codes,
speed-weighted gamified scoring, live leaderboards, and teacher pacing.
"""
import random
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.live_session import LiveSession, LiveParticipant
from app.models.quiz import Quiz
from app.models.question import Question


class LiveQuizService:
    @staticmethod
    def _generate_pin() -> str:
        chars = "".join(c for c in string.digits if c not in "01")
        return "LIVE-" + "".join(random.choices(chars, k=4))

    @staticmethod
    def create_session(db: Session, teacher_id: int, quiz_id: int, mode: str = "instructor_paced") -> Dict[str, Any]:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")
        if quiz.created_by_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: quiz owned by another teacher.")

        q_count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
        if q_count == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start a live session for a quiz with no questions.")

        pin = LiveQuizService._generate_pin()
        session = LiveSession(
            session_pin=pin,
            quiz_id=quiz.id,
            teacher_id=teacher_id,
            status="lobby",
            current_question_index=0,
            mode=mode,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return {
            "session_id": session.id,
            "session_pin": session.session_pin,
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
            "total_questions": q_count,
            "status": session.status,
            "mode": session.mode,
        }

    @staticmethod
    def join_session(db: Session, pin: str, nickname: str) -> Dict[str, Any]:
        clean_pin = pin.strip().upper()
        session = db.query(LiveSession).filter(LiveSession.session_pin == clean_pin).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Live session PIN not found. Please check your code.")

        if session.status == "ended":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This live session has already concluded.")

        token = secrets.token_urlsafe(20)
        part = LiveParticipant(
            session_id=session.id,
            participant_token=token,
            nickname=nickname.strip()[:30] or "Anonymous Player",
            score=0,
            streak=0,
            correct_count=0,
        )
        db.add(part)
        db.commit()
        db.refresh(part)

        quiz = db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
        return {
            "participant_token": token,
            "nickname": part.nickname,
            "session_pin": session.session_pin,
            "quiz_title": quiz.title if quiz else "Live Assessment",
            "status": session.status,
        }

    @staticmethod
    def get_session_state(db: Session, pin: str, participant_token: Optional[str] = None) -> Dict[str, Any]:
        clean_pin = pin.strip().upper()
        session = db.query(LiveSession).filter(LiveSession.session_pin == clean_pin).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        quiz = db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
        questions = (
            db.query(Question)
            .filter(Question.quiz_id == session.quiz_id)
            .order_by(Question.order_index.asc(), Question.id.asc())
            .all()
        )
        total_q = len(questions)

        current_q_data = None
        if session.status == "active" and 0 <= session.current_question_index < total_q:
            cq = questions[session.current_question_index]
            current_q_data = {
                "question_id": cq.id,
                "question_index": session.current_question_index + 1,
                "total_questions": total_q,
                "question_text": cq.question_text,
                "option_a": cq.option_a,
                "option_b": cq.option_b,
                "option_c": cq.option_c,
                "option_d": cq.option_d,
                "marks": cq.marks,
            }

        # Leaderboard Top 5
        top_parts = (
            db.query(LiveParticipant)
            .filter(LiveParticipant.session_id == session.id)
            .order_by(LiveParticipant.score.desc())
            .limit(5)
            .all()
        )
        leaderboard = [
            {"rank": idx + 1, "nickname": p.nickname, "score": p.score, "streak": p.streak}
            for idx, p in enumerate(top_parts)
        ]

        total_participants = db.query(LiveParticipant).filter(LiveParticipant.session_id == session.id).count()

        # Participant individual state
        my_stats = None
        if participant_token:
            p_obj = db.query(LiveParticipant).filter(LiveParticipant.participant_token == participant_token).first()
            if p_obj:
                my_stats = {
                    "nickname": p_obj.nickname,
                    "score": p_obj.score,
                    "streak": p_obj.streak,
                    "correct_count": p_obj.correct_count,
                }

        return {
            "session_pin": session.session_pin,
            "quiz_title": quiz.title if quiz else "Live Assessment",
            "status": session.status,
            "current_question_index": session.current_question_index + 1,
            "total_questions": total_q,
            "current_question": current_q_data,
            "total_participants": total_participants,
            "leaderboard": leaderboard,
            "my_stats": my_stats,
        }

    @staticmethod
    def start_session(db: Session, pin: str, teacher_id: int) -> Dict[str, Any]:
        clean_pin = pin.strip().upper()
        session = db.query(LiveSession).filter(LiveSession.session_pin == clean_pin).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        if session.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        session.status = "active"
        session.current_question_index = 0
        db.commit()
        return {"status": "active", "current_question_index": 1}

    @staticmethod
    def next_question(db: Session, pin: str, teacher_id: int) -> Dict[str, Any]:
        clean_pin = pin.strip().upper()
        session = db.query(LiveSession).filter(LiveSession.session_pin == clean_pin).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        if session.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        total_q = db.query(Question).filter(Question.quiz_id == session.quiz_id).count()
        next_idx = session.current_question_index + 1
        if next_idx >= total_q:
            session.status = "ended"
            session.ended_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "ended", "message": "All questions completed. Showing final podium."}
        else:
            session.current_question_index = next_idx
            db.commit()
            return {"status": "active", "current_question_index": next_idx + 1}

    @staticmethod
    def submit_answer(
        db: Session,
        pin: str,
        participant_token: str,
        question_id: int,
        selected_option: str,
        time_spent_sec: float = 5.0,
    ) -> Dict[str, Any]:
        session = db.query(LiveSession).filter(LiveSession.session_pin == pin.strip().upper()).first()
        if not session or session.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Live session is not actively accepting answers.")

        part = db.query(LiveParticipant).filter(LiveParticipant.participant_token == participant_token).first()
        if not part:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant token invalid.")

        question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == session.quiz_id).first()
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

        is_correct = (selected_option.strip().upper() == question.correct_option.strip().upper())
        points_earned = 0
        if is_correct:
            # Gamified speed points: 600 base + up to 400 speed bonus
            speed_bonus = max(0, int(400 * (1 - min(30.0, time_spent_sec) / 30.0)))
            points_earned = 600 + speed_bonus
            part.score += points_earned
            part.streak += 1
            part.correct_count += 1
        else:
            part.streak = 0

        part.last_active_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "is_correct": is_correct,
            "points_earned": points_earned,
            "total_score": part.score,
            "streak": part.streak,
            "correct_option": question.correct_option,
            "explanation": question.explanation,
        }

    @staticmethod
    def end_session(db: Session, pin: str, teacher_id: int) -> Dict[str, Any]:
        session = db.query(LiveSession).filter(LiveSession.session_pin == pin.strip().upper()).first()
        if not session or session.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        session.status = "ended"
        session.ended_at = datetime.now(timezone.utc)
        db.commit()

        # Top 3 Podium
        podium = (
            db.query(LiveParticipant)
            .filter(LiveParticipant.session_id == session.id)
            .order_by(LiveParticipant.score.desc())
            .limit(3)
            .all()
        )
        return {
            "status": "ended",
            "podium": [
                {"rank": idx + 1, "nickname": p.nickname, "score": p.score, "correct_count": p.correct_count}
                for idx, p in enumerate(podium)
            ],
        }
