"""
Quiz Attempt and Answer Pydantic Schemas.
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.question import QuestionStudentResponse


class AnswerSubmitRequest(BaseModel):
    question_id: int
    selected_option: Optional[str] = None  # None to deselect, or 'A', 'B', 'C', 'D'

    @field_validator("selected_option")
    @classmethod
    def validate_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            upper = v.upper()
            if upper not in {"A", "B", "C", "D"}:
                raise ValueError("Selected option must be 'A', 'B', 'C', or 'D'")
            return upper
        return None


class AnswerSubmitResponse(BaseModel):
    attempt_id: int
    question_id: int
    selected_option: Optional[str]
    saved: bool


class AttemptStartResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    duration_minutes: int
    start_time: datetime
    deadline_time: datetime
    questions: List[QuestionStudentResponse]
    saved_answers: Dict[int, Optional[str]] = {}
    max_attempts: int = 1
    attempt_number: int = 1


class QuestionReviewItem(BaseModel):
    question_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    selected_option: Optional[str]
    correct_option: Optional[str] = None
    is_correct: bool = False
    marks_awarded: float = 0.0
    max_marks: int = 1
    explanation: Optional[str] = None


class AttemptResultResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    student_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    deadline_time: datetime
    score_obtained: float
    total_marks: float
    percentage: float
    passing_percentage: int
    is_passed: bool
    total_questions: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    results_released: bool = True
    review: Optional[List[QuestionReviewItem]] = None


class AttemptSummaryResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    score_obtained: float
    total_marks: float
    percentage: float
    is_passed: bool
    results_released: bool = True

    model_config = ConfigDict(from_attributes=True)


class StudentDashboardStatsResponse(BaseModel):
    total_attempts: int = 0
    average_score: float = 0.0
    pass_rate: float = 0.0
    rank_text: str = "Top 15%"
    recent_results: List[dict] = []
    progress_trend: List[dict] = []
