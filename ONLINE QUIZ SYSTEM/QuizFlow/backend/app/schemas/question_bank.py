"""
Question Bank Pydantic Schemas for QuizFlow 2.0.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuestionBankItemBase(BaseModel):
    question_text: str = Field(..., min_length=3)
    question_type: str = "single_choice"
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: str = "A"
    correct_answers: Optional[str] = None
    marks: int = Field(1, ge=1, le=100)
    explanation: Optional[str] = None
    cognitive_level: str = "understand"
    difficulty: str = "medium"


class QuestionBankItemCreate(QuestionBankItemBase):
    pass


class QuestionBankItemUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: Optional[str] = None
    correct_answers: Optional[str] = None
    marks: Optional[int] = None
    explanation: Optional[str] = None
    cognitive_level: Optional[str] = None
    difficulty: Optional[str] = None


class QuestionBankItemResponse(QuestionBankItemBase):
    id: int
    bank_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionBankBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    subject: str = "General"
    grade_level: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str = "medium"
    tags: Optional[str] = None


class QuestionBankCreate(QuestionBankBase):
    pass


class QuestionBankUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[str] = None


class QuestionBankResponse(QuestionBankBase):
    id: int
    teacher_id: int
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    items: Optional[List[QuestionBankItemResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class ImportFromBankRequest(BaseModel):
    item_ids: List[int]
