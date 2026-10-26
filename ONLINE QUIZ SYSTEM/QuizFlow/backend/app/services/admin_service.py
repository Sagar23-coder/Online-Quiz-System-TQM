"""
Admin Statistics and Platform Management Service.
Calculates real aggregates from the database for global administration, user control, moderation, and audit logs.
"""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.attempt import AttemptStatus, QuizAttempt
from app.models.audit_log import AuditLog
from app.models.quiz import Quiz
from app.models.user import User, UserRole
from app.schemas.admin import (
    DashboardStatsResponse,
    PlatformReportsResponse,
    RecentActivityItem,
    ResultListItem,
    UserManagementItem,
)
from app.schemas.user import AuditLogResponse
from app.services.audit_service import AuditService


class AdminService:
    @staticmethod
    def get_dashboard_stats(db: Session) -> DashboardStatsResponse:
        total_users = db.query(User).count()
        total_participants = db.query(User).filter(
            User.role.in_([UserRole.PARTICIPANT.value, UserRole.STUDENT.value])
        ).count()
        total_organizers = db.query(User).filter(User.role == UserRole.ORGANIZER.value).count()

        total_quizzes = db.query(Quiz).count()
        published_quizzes = db.query(Quiz).filter(Quiz.is_published == True, Quiz.is_disabled == False).count()  # noqa: E712
        draft_quizzes = db.query(Quiz).filter(Quiz.is_published == False).count()  # noqa: E712
        disabled_quizzes = db.query(Quiz).filter(Quiz.is_disabled == True).count()  # noqa: E712

        total_attempts = db.query(QuizAttempt).count()
        completed_attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.status.in_([AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value]))
            .count()
        )

        passed_attempts = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.status.in_([AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value]),
                QuizAttempt.is_passed == True,  # noqa: E712
            )
            .count()
        )

        scores = [
            a.percentage
            for a in db.query(QuizAttempt)
            .filter(QuizAttempt.status.in_([AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value]))
            .all()
        ]
        average_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        average_pass_rate = (
            round((passed_attempts / completed_attempts) * 100.0, 1) if completed_attempts > 0 else 0.0
        )

        recent = (
            db.query(QuizAttempt)
            .order_by(QuizAttempt.created_at.desc())
            .limit(8)
            .all()
        )

        recent_items: List[RecentActivityItem] = []
        for a in recent:
            student = db.query(User).filter(User.id == a.student_id).first()
            quiz = db.query(Quiz).filter(Quiz.id == a.quiz_id).first()
            recent_items.append(
                RecentActivityItem(
                    attempt_id=a.id,
                    student_name=student.full_name if student else "Unknown",
                    quiz_title=quiz.title if quiz else "Quiz",
                    score_obtained=a.score_obtained,
                    total_marks=a.total_marks,
                    percentage=a.percentage,
                    is_passed=a.is_passed,
                    status=a.status,
                    submitted_at=a.end_time or a.start_time,
                )
            )

        # Recent registered users for Admin panel
        recent_users_db = db.query(User).order_by(User.created_at.desc()).limit(5).all()
        recent_users_list = [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in recent_users_db
        ]

        # Activity overview: attempts trend over past 7 days
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        activity_overview = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            attempts_cnt = db.query(QuizAttempt).filter(
                QuizAttempt.created_at >= day_start,
                QuizAttempt.created_at <= day_end
            ).count()
            quizzes_cnt = db.query(Quiz).filter(
                Quiz.created_at >= day_start,
                Quiz.created_at <= day_end
            ).count()
            activity_overview.append({
                "date": day.strftime("%b %d"),
                "attempts": attempts_cnt,
                "quizzes": quizzes_cnt,
            })

        return DashboardStatsResponse(
            total_users=total_users,
            total_students=total_participants,
            total_participants=total_participants,
            total_organizers=total_organizers,
            total_quizzes=total_quizzes,
            published_quizzes=published_quizzes,
            draft_quizzes=draft_quizzes,
            disabled_quizzes=disabled_quizzes,
            total_attempts=total_attempts,
            completed_attempts=completed_attempts,
            average_score=average_score,
            average_pass_rate=average_pass_rate,
            recent_activity=recent_items,
            recent_users=recent_users_list,
            activity_overview=activity_overview,
        )

    @staticmethod
    def get_users_list(
        db: Session,
        role: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[UserManagementItem]:
        query = db.query(User)

        if role:
            clean_role = role.strip().lower()
            if clean_role in ("participant", "student"):
                query = query.filter(User.role.in_([UserRole.PARTICIPANT.value, UserRole.STUDENT.value]))
            else:
                query = query.filter(User.role == clean_role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search:
            s = f"%{search.strip().lower()}%"
            query = query.filter((func.lower(User.email).like(s)) | (func.lower(User.full_name).like(s)))

        users = query.order_by(User.created_at.desc()).all()

        results: List[UserManagementItem] = []
        for u in users:
            quizzes_created = db.query(Quiz).filter(Quiz.created_by_id == u.id).count()
            attempts_count = db.query(QuizAttempt).filter(QuizAttempt.student_id == u.id).count()

            avg_pct = (
                db.query(func.avg(QuizAttempt.percentage))
                .filter(
                    QuizAttempt.student_id == u.id,
                    QuizAttempt.status.in_([AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value]),
                )
                .scalar()
                or 0.0
            )

            results.append(
                UserManagementItem(
                    id=u.id,
                    email=u.email,
                    full_name=u.full_name,
                    role="participant" if u.role == "student" else u.role,
                    is_active=u.is_active,
                    created_at=u.created_at,
                    quizzes_created=quizzes_created,
                    attempts_count=attempts_count,
                    avg_percentage=round(float(avg_pct), 1),
                )
            )
        return results

    # Backward compatibility alias
    @staticmethod
    def get_students_list(db: Session) -> List[UserManagementItem]:
        return AdminService.get_users_list(db, role="participant")

    @staticmethod
    def set_user_status(
        db: Session,
        user_id: int,
        is_active: bool,
        admin_id: int,
        reason: Optional[str] = None,
    ) -> UserManagementItem:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot suspend their own account.",
            )

        if user.role == UserRole.ADMIN.value and not is_active:
            other_admins = (
                db.query(User)
                .filter(User.role == UserRole.ADMIN.value, User.id != user_id, User.is_active == True)  # noqa: E712
                .count()
            )
            if other_admins == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the sole remaining active administrator.",
                )

        user.is_active = is_active
        db.commit()
        db.refresh(user)

        action_name = "USER_REACTIVATE" if is_active else "USER_SUSPEND"
        AuditService.log(
            db,
            action=action_name,
            user_id=admin_id,
            resource_type="user",
            resource_id=user.id,
            details={"email": user.email, "is_active": is_active, "reason": reason},
        )

        quizzes_cnt = db.query(Quiz).filter(Quiz.created_by_id == user.id).count()
        attempts_cnt = db.query(QuizAttempt).filter(QuizAttempt.student_id == user.id).count()
        return UserManagementItem(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            quizzes_created=quizzes_cnt,
            attempts_count=attempts_cnt,
            avg_percentage=0.0,
        )

    @staticmethod
    def moderate_quiz(
        db: Session,
        quiz_id: int,
        is_disabled: bool,
        admin_id: int,
        reason: Optional[str] = None,
    ) -> bool:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        quiz.is_disabled = is_disabled
        db.commit()

        action_name = "QUIZ_MODERATE_DISABLE" if is_disabled else "QUIZ_MODERATE_ENABLE"
        AuditService.log(
            db,
            action=action_name,
            user_id=admin_id,
            resource_type="quiz",
            resource_id=quiz.id,
            details={"title": quiz.title, "is_disabled": is_disabled, "reason": reason},
        )
        return True

    @staticmethod
    def get_audit_logs(
        db: Session,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLogResponse]:
        query = db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action == action.upper())
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

        results = []
        for log_entry in logs:
            u_email = None
            if log_entry.user_id:
                u = db.query(User).filter(User.id == log_entry.user_id).first()
                if u:
                    u_email = u.email

            results.append(
                AuditLogResponse(
                    id=log_entry.id,
                    user_id=log_entry.user_id,
                    user_email=u_email,
                    action=log_entry.action,
                    resource_type=log_entry.resource_type,
                    resource_id=log_entry.resource_id,
                    details=log_entry.details,
                    ip_address=log_entry.ip_address,
                    created_at=log_entry.created_at,
                )
            )
        return results

    @staticmethod
    def get_platform_reports(db: Session) -> PlatformReportsResponse:
        total_participants = db.query(User).filter(
            User.role.in_([UserRole.PARTICIPANT.value, UserRole.STUDENT.value])
        ).count()
        total_organizers = db.query(User).filter(User.role == UserRole.ORGANIZER.value).count()
        total_admins = db.query(User).filter(User.role == UserRole.ADMIN.value).count()

        role_dist = {
            "participants": total_participants,
            "organizers": total_organizers,
            "admins": total_admins,
        }

        pub_cnt = db.query(Quiz).filter(Quiz.is_published == True, Quiz.is_disabled == False).count()  # noqa: E712
        draft_cnt = db.query(Quiz).filter(Quiz.is_published == False).count()  # noqa: E712
        disabled_cnt = db.query(Quiz).filter(Quiz.is_disabled == True).count()  # noqa: E712

        quiz_dist = {
            "published": pub_cnt,
            "draft": draft_cnt,
            "disabled": disabled_cnt,
        }

        completed_cnt = db.query(QuizAttempt).filter(QuizAttempt.status == AttemptStatus.COMPLETED.value).count()
        in_prog_cnt = db.query(QuizAttempt).filter(QuizAttempt.status == AttemptStatus.IN_PROGRESS.value).count()
        expired_cnt = db.query(QuizAttempt).filter(QuizAttempt.status == AttemptStatus.EXPIRED.value).count()

        attempt_dist = {
            "completed": completed_cnt,
            "in_progress": in_prog_cnt,
            "expired": expired_cnt,
        }

        passed_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.status.in_([AttemptStatus.COMPLETED.value, AttemptStatus.EXPIRED.value]),
            QuizAttempt.is_passed == True,  # noqa: E712
        ).count()
        tot_finished = completed_cnt + expired_cnt
        pass_rate = round((passed_attempts / tot_finished) * 100.0, 1) if tot_finished > 0 else 0.0

        return PlatformReportsResponse(
            role_distribution=role_dist,
            quiz_status_distribution=quiz_dist,
            attempt_status_distribution=attempt_dist,
            pass_rate=pass_rate,
        )

    @staticmethod
    def get_all_results(db: Session) -> List[ResultListItem]:
        attempts = (
            db.query(QuizAttempt)
            .order_by(QuizAttempt.created_at.desc())
            .all()
        )

        results: List[ResultListItem] = []
        for a in attempts:
            student = db.query(User).filter(User.id == a.student_id).first()
            quiz = db.query(Quiz).filter(Quiz.id == a.quiz_id).first()
            results.append(
                ResultListItem(
                    attempt_id=a.id,
                    student_id=a.student_id,
                    student_name=student.full_name if student else "Unknown",
                    student_email=student.email if student else "N/A",
                    quiz_id=a.quiz_id,
                    quiz_title=quiz.title if quiz else "Quiz",
                    status=a.status,
                    score_obtained=a.score_obtained,
                    total_marks=a.total_marks,
                    percentage=a.percentage,
                    is_passed=a.is_passed,
                    start_time=a.start_time,
                    end_time=a.end_time,
                )
            )
        return results
