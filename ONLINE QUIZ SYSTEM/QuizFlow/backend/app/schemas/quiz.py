"""
Quiz Pydantic Schemas with Multi-Role, Join Codes, Scheduling, and Reporting.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QuizBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    subject: Optional[str] = "General"
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: int = Field(30, ge=1, le=300)
    passing_percentage: int = Field(50, ge=1, le=100)
    is_public: bool = True
    max_attempts: int = Field(1, ge=1, le=10)
    release_results_immediately: bool = True
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class QuizCreate(QuizBase):
    pass


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    subject: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=300)
    passing_percentage: Optional[int] = Field(None, ge=1, le=100)
    is_published: Optional[bool] = None
    is_public: Optional[bool] = None
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    release_results_immediately: Optional[bool] = None
    results_released: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class QuizAdminResponse(QuizBase):
    id: int
    total_marks: int
    is_published: bool
    join_code: Optional[str] = None
    results_released: bool = True
    is_disabled: bool = False
    created_by_id: int
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    question_count: int = 0
    attempt_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class QuizStudentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: int
    passing_percentage: int
    total_marks: int
    question_count: int = 0
    join_code: Optional[str] = None
    is_public: bool = True
    creator_name: Optional[str] = None
    max_attempts: int = 1
    attempts_taken: int = 0
    results_released: bool = True

    model_config = ConfigDict(from_attributes=True)


class QuizDetailStudentResponse(QuizStudentResponse):
    pass


class JoinCodeRequest(BaseModel):
    join_code: str = Field(..., min_length=3, max_length=16)


class QuestionPerformanceStat(BaseModel):
    question_id: int
    question_text: str
    total_answers: int
    correct_answers: int
    accuracy_percentage: float
    topic: Optional[str] = "General"
    difficulty: Optional[str] = "medium"
    common_wrong_option: Optional[str] = None
    common_wrong_count: int = 0
    common_wrong_percentage: float = 0.0
    misconception_note: Optional[str] = None


class ParticipantAttemptItem(BaseModel):
    attempt_id: int
    student_id: int
    student_name: str
    student_email: str
    status: str
    score_obtained: float
    total_marks: float
    percentage: float
    is_passed: bool
    submitted_at: Optional[datetime] = None


class QuizReportResponse(BaseModel):
    quiz_id: int
    title: str
    subject: Optional[str] = "General"
    join_code: Optional[str]
    is_published: bool
    results_released: bool
    total_marks: int
    passing_percentage: int
    total_attempts: int
    unique_participants: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_count: int
    fail_count: int
    pass_percentage: float
    attempts: List[ParticipantAttemptItem] = []
    question_stats: List[QuestionPerformanceStat] = []
    misconceptions: List[dict] = []
    topic_breakdown: List[dict] = []
    recommended_actions: List[dict] = []


class OrganizerDashboardStats(BaseModel):
    total_quizzes: int
    published_quizzes: int
    draft_quizzes: int
    total_participants: int
    total_attempts: int
    average_score: float


# AI & File Generation Schemas
class AIGenerateQuizRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1500)
    num_questions: int = Field(5, ge=1, le=20)
    difficulty: str = Field("medium")
    topic: Optional[str] = None
    save_directly: bool = False


class AIImportFileQuizRequest(BaseModel):
    file_content: str = Field(..., min_length=5)
    filename: str = Field(..., min_length=1)
    num_questions: int = Field(5, ge=1, le=20)
    difficulty: str = Field("medium")
    save_directly: bool = False


class AIGeneratedQuestionItem(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: Optional[str] = None
    topic: Optional[str] = "General"
    difficulty: Optional[str] = "medium"
    learning_objective: Optional[str] = ""
    marks: int = 1


class AIGeneratedQuizResponse(BaseModel):
    title: str
    description: Optional[str] = None
    subject: Optional[str] = "General"
    duration_minutes: int = 30
    passing_percentage: int = 50
    questions: List[AIGeneratedQuestionItem] = []
    quiz_id: Optional[int] = None
    join_code: Optional[str] = None
    source: str = "ai_generated"
