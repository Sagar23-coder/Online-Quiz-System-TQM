"""
Live Synchronized Assessment Session Models for QuizFlow 2.0.
Supports real-time classroom gamified assessments with 6-digit PIN join codes,
speed-weighted scoring, live leaderboards, and teacher session pacing.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base


class LiveSession(Base):
    __tablename__ = "live_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_pin = Column(String(16), unique=True, index=True, nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="lobby", nullable=False)  # lobby, active, paused, ended
    current_question_index = Column(Integer, default=0, nullable=False)
    mode = Column(String(30), default="instructor_paced", nullable=False)  # instructor_paced or student_paced
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    quiz = relationship("Quiz")
    teacher = relationship("User")
    participants = relationship("LiveParticipant", back_populates="session", cascade="all, delete-orphan")


class LiveParticipant(Base):
    __tablename__ = "live_participants"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("live_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_token = Column(String(64), unique=True, index=True, nullable=False)
    nickname = Column(String(50), nullable=False)
    score = Column(Integer, default=0, nullable=False)
    streak = Column(Integer, default=0, nullable=False)
    correct_count = Column(Integer, default=0, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_active_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    session = relationship("LiveSession", back_populates="participants")
