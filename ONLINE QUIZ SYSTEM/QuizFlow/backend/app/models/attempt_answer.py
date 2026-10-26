"""
Attempt Answer Model for QuizFlow.
Stores per-question responses submitted by a student during an active attempt.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option = Column(String(1), nullable=True)  # 'A', 'B', 'C', 'D', or None
    is_correct = Column(Boolean, default=False, nullable=False)
    marks_awarded = Column(Float, default=0.0, nullable=False)
    answered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question", back_populates="attempt_answers")

    def __repr__(self) -> str:
        return f"<AttemptAnswer attempt={self.attempt_id} question={self.question_id} opt={self.selected_option}>"
