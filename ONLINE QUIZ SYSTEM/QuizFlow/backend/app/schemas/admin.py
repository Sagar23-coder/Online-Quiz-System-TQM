"""
Admin Dashboard, User Management, Audit Trail, and Results Pydantic Schemas.
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class RecentActivityItem(BaseModel):
    attempt_id: int
    student_name: str
    quiz_title: str
    score_obtained: float = 0.0
    total_marks: float = 0.0
    percentage: float
    is_passed: bool
    status: str
    submitted_at: Optional[datetime]


class DashboardStatsResponse(BaseModel):
    total_users: int = 0
    total_students: int = 0  # Backward-compatibility (total participants)
    total_participants: int = 0
    total_organizers: int = 0
    total_quizzes: int = 0
    published_quizzes: int = 0
    draft_quizzes: int = 0
    closed_quizzes: int = 0
    disabled_quizzes: int = 0
    total_attempts: int = 0
    completed_attempts: int = 0
    average_score: float = 0.0
    average_pass_rate: float = 0.0
    recent_activity: List[RecentActivityItem] = []
    recent_users: List[dict] = []
    activity_overview: List[dict] = []


class UserManagementItem(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    quizzes_created: int = 0
    attempts_count: int = 0
    avg_percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# Backward-compatibility alias
StudentListItem = UserManagementItem


class ResultListItem(BaseModel):
    attempt_id: int
    student_id: int
    student_name: str
    student_email: str
    quiz_id: int
    quiz_title: str
    status: str
    score_obtained: float
    total_marks: float
    percentage: float
    is_passed: bool
    start_time: datetime
    end_time: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class QuizModerationRequest(BaseModel):
    is_disabled: bool
    reason: Optional[str] = None


class PlatformReportsResponse(BaseModel):
    role_distribution: Dict[str, int]
    quiz_status_distribution: Dict[str, int]
    attempt_status_distribution: Dict[str, int]
    pass_rate: float
