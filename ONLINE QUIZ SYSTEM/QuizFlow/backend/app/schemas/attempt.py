"""
Quiz Attempt and Answer Pydantic Schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    student_option: Optional[str] = None
    correct_option: Optional[str] = None
    is_correct: bool = False
    marks_awarded: float = 0.0
    max_marks: int = 1
    explanation: Optional[str] = None


class SubmitAttemptRequest(BaseModel):
    answers: Optional[Dict[int, Optional[str]]] = None


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


# =========================================================================
# Public Link-Based Student Quiz Participation Schemas (No Login Required)
# =========================================================================

class PublicStudentDetailsRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    student_class: str = Field(..., min_length=1, max_length=50)
    section: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None


class PublicQuizInfoResponse(BaseModel):
    title: str
    subject: Optional[str] = "General"
    description: Optional[str] = None
    instructions: Optional[str] = None
    teacher_name: Optional[str] = "Instructor"
    duration_minutes: int
    total_questions: int
    total_marks: int
    passing_percentage: int
    is_published: bool
    is_active: bool
    max_attempts: int = 1
    mode: str = "exam"
    shuffle_questions: bool = True
    shuffle_options: bool = True
    result_release_policy: str = "immediate"


class PublicAttemptStartResponse(BaseModel):
    attempt_token: str
    quiz_title: str
    student_name: str
    student_class: str
    student_section: str
    duration_minutes: int
    start_time: datetime
    deadline_time: datetime
    remaining_seconds: int
    questions: List[QuestionStudentResponse]
    saved_answers: Dict[int, Optional[str]] = {}
    mode: str = "exam"


class PracticeCheckRequest(BaseModel):
    question_id: int
    selected_option: str


class PracticeCheckResponse(BaseModel):
    question_id: int
    is_correct: bool
    correct_option: str
    explanation: Optional[str] = None
    hint: Optional[str] = None


class IntegrityEventRequest(BaseModel):
    event_type: str
    client_timestamp: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PublicAttemptResultResponse(BaseModel):
    attempt_token: str
    quiz_title: str
    student_name: str
    student_class: Optional[str] = None
    student_section: Optional[str] = None
    score_obtained: float
    total_marks: float
    percentage: float
    passing_percentage: int
    is_passed: bool
    total_questions: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    submitted_at: Optional[datetime] = None
    results_released: bool = True
    review: Optional[List[QuestionReviewItem]] = None
