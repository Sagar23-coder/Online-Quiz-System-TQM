"""
Question Pydantic Schemas for QuizFlow.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=3)
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    marks: int = Field(1, ge=1, le=100)
    explanation: Optional[str] = None
    topic: Optional[str] = "General"
    difficulty: Optional[str] = "medium"
    learning_objective: Optional[str] = ""
    order_index: int = Field(0, ge=0)


class QuestionCreate(QuestionBase):
    correct_option: str = Field(..., min_length=1, max_length=1)

    @field_validator("correct_option")
    @classmethod
    def validate_option(cls, v: str) -> str:
        upper = v.upper()
        if upper not in {"A", "B", "C", "D"}:
            raise ValueError("correct_option must be 'A', 'B', 'C', or 'D'")
        return upper


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(None, min_length=3)
    option_a: Optional[str] = Field(None, min_length=1)
    option_b: Optional[str] = Field(None, min_length=1)
    option_c: Optional[str] = Field(None, min_length=1)
    option_d: Optional[str] = Field(None, min_length=1)
    correct_option: Optional[str] = Field(None, min_length=1, max_length=1)
    marks: Optional[int] = Field(None, ge=1, le=100)
    explanation: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    learning_objective: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)

    @field_validator("correct_option")
    @classmethod
    def validate_option(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            upper = v.upper()
            if upper not in {"A", "B", "C", "D"}:
                raise ValueError("correct_option must be 'A', 'B', 'C', or 'D'")
            return upper
        return v


class QuestionAdminResponse(QuestionBase):
    id: int
    quiz_id: int
    correct_option: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionStudentResponse(BaseModel):
    id: int
    quiz_id: Optional[int] = None
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    marks: int
    order_index: int = 0

    model_config = ConfigDict(from_attributes=True)
