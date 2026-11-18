"""
Question Bank and Question Bank Item Models for QuizFlow 2.0.
Provides reusable curriculum question repositories organized by subject, chapter, topic,
difficulty, and cognitive taxonomy (Bloom's).
Strictly scoped to teacher multi-tenancy.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class QuestionBank(Base):
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), default="General", nullable=False, index=True)
    grade_level = Column(String(50), nullable=True)
    topic = Column(String(100), nullable=True)
    difficulty = Column(String(20), default="medium", nullable=False)
    tags = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    teacher = relationship("User")
    items = relationship("QuestionBankItem", back_populates="bank", cascade="all, delete-orphan")


class QuestionBankItem(Base):
    __tablename__ = "question_bank_items"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), default="single_choice", nullable=False)  # single_choice, multi_select, true_false, short_answer, numeric, ordering
    option_a = Column(Text, nullable=True)
    option_b = Column(Text, nullable=True)
    option_c = Column(Text, nullable=True)
    option_d = Column(Text, nullable=True)
    correct_option = Column(String(10), default="A", nullable=False)
    correct_answers = Column(Text, nullable=True)  # JSON-encoded array for multi-select, ordering or range
    marks = Column(Integer, default=1, nullable=False)
    explanation = Column(Text, nullable=True)
    cognitive_level = Column(String(30), default="understand", nullable=False)  # remember, understand, apply, analyze, evaluate
    difficulty = Column(String(20), default="medium", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    bank = relationship("QuestionBank", back_populates="items")
