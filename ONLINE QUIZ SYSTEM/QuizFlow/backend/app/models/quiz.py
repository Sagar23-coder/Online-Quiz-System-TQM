"""
Quiz Model for QuizFlow.
Supports organizer ownership, join codes, scheduling, attempt limits, and result release controls.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    subject = Column(String(100), default="General", nullable=True, index=True)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=30, nullable=False)
    passing_percentage = Column(Integer, default=50, nullable=False)
    total_marks = Column(Integer, default=0, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)

    # Advanced Quiz Controls
    join_code = Column(String(16), unique=True, index=True, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    max_attempts = Column(Integer, default=1, nullable=False)
    release_results_immediately = Column(Boolean, default=True, nullable=False)
    results_released = Column(Boolean, default=True, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    is_disabled = Column(Boolean, default=False, nullable=False)  # Admin moderation flag

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    creator = relationship("User", back_populates="quizzes_created")
    questions = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Quiz id={self.id} title='{self.title}' code='{self.join_code}' published={self.is_published}>"
