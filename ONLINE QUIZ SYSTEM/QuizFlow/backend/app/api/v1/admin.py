"""
Admin Statistics, User Management, Quiz Moderation, and Audit Log Endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.models.user import User
from app.schemas.admin import (
    DashboardStatsResponse,
    PlatformReportsResponse,
    QuizModerationRequest,
    ResultListItem,
    UserManagementItem,
)
from app.schemas.user import AuditLogResponse, UserStatusUpdate
from app.services.admin_service import AdminService

router = APIRouter()


@router.get(
    "/dashboard-stats",
    response_model=DashboardStatsResponse,
    summary="Get aggregated statistics for admin dashboard",
)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Returns real metrics computed from database: total users, participants, organizers,
    quizzes, pass rates, and recent activity.
    """
    return AdminService.get_dashboard_stats(db)


@router.get(
    "/users",
    response_model=List[UserManagementItem],
    summary="List and search platform users with role and status filters (Admin only)",
)
def list_users(
    role: Optional[str] = Query(None, description="Filter by role: admin, organizer, participant"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    is_active: Optional[bool] = Query(None, description="Filter active/suspended accounts"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.get_users_list(db, role=role, search=search, is_active=is_active)


# Backward compatibility
@router.get(
    "/students",
    response_model=List[UserManagementItem],
    summary="List all registered students/participants (Admin only)",
)
def list_students(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.get_students_list(db)


@router.post(
    "/users/{user_id}/status",
    response_model=UserManagementItem,
    summary="Suspend or reactivate a user account (Admin only)",
)
def set_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Suspends or reactivates a user account. Suspended users cannot authenticate.
    Prevents self-suspension and deactivating the last active administrator.
    """
    return AdminService.set_user_status(
        db,
        user_id=user_id,
        is_active=payload.is_active,
        admin_id=current_admin.id,
        reason=payload.reason,
    )


@router.post(
    "/quizzes/{quiz_id}/moderate",
    summary="Moderate a quiz: disable or re-enable (Admin only)",
)
def moderate_quiz(
    quiz_id: int,
    payload: QuizModerationRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Administratively disables or re-enables a quiz without deleting history or ownership.
    """
    AdminService.moderate_quiz(
        db,
        quiz_id=quiz_id,
        is_disabled=payload.is_disabled,
        admin_id=current_admin.id,
        reason=payload.reason,
    )
    action = "disabled" if payload.is_disabled else "re-enabled"
    return {"message": f"Quiz {action} successfully.", "quiz_id": quiz_id, "is_disabled": payload.is_disabled}


@router.get(
    "/audit-logs",
    response_model=List[AuditLogResponse],
    summary="List platform security and activity audit logs (Admin only)",
)
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action code"),
    user_id: Optional[int] = Query(None, description="Filter by actor user ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.get_audit_logs(db, action=action, user_id=user_id, limit=limit, offset=offset)


@router.get(
    "/platform-reports",
    response_model=PlatformReportsResponse,
    summary="Get platform-wide distribution reports and trends (Admin only)",
)
def get_platform_reports(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.get_platform_reports(db)


@router.get(
    "/results",
    response_model=List[ResultListItem],
    summary="List all quiz attempt results across students (Admin only)",
)
def list_all_results(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.get_all_results(db)
