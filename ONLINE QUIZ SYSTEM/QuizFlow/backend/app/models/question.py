"""
Question Model for QuizFlow (Multiple-Choice Questions).
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    marks = Column(Integer, default=1, nullable=False)
    explanation = Column(Text, nullable=True)
    topic = Column(String(100), default="General", nullable=True, index=True)
    difficulty = Column(String(20), default="medium", nullable=True, index=True)
    learning_objective = Column(String(255), default="", nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    attempt_answers = relationship("AttemptAnswer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Question id={self.id} quiz_id={self.quiz_id} correct={self.correct_option}>"
