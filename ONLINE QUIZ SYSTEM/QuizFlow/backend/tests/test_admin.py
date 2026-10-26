"""
Tests for Admin analytics, students management, and results log.
"""
from app.core.config import settings
from app.database.init_db import bootstrap_admin
from app.models.user import User, UserRole


def test_admin_bootstrap_requires_explicit_credentials(db_session, monkeypatch):
    monkeypatch.setattr(settings, "FIRST_SUPERUSER_EMAIL", "")
    monkeypatch.setattr(settings, "FIRST_SUPERUSER_PASSWORD", "")

    assert bootstrap_admin(db=db_session) is False
    assert db_session.query(User).filter(User.role == UserRole.ADMIN.value).count() == 0


def test_admin_dashboard_stats(client, admin_token, student_user):
    response = client.get(
        "/api/v1/admin/dashboard-stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_students" in data
    assert "total_quizzes" in data
    assert "published_quizzes" in data
    assert "total_attempts" in data
    assert "completed_attempts" in data
    assert "average_pass_rate" in data
    assert "recent_activity" in data
    assert data["total_students"] >= 1


def test_admin_students_list(client, admin_token, student_user):
    response = client.get(
        "/api/v1/admin/students",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    student_emails = [s["email"] for s in data]
    assert student_user.email in student_emails


def test_admin_results_list(client, admin_token):
    response = client.get(
        "/api/v1/admin/results",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_admin_endpoints_forbidden_for_students(client, student_token):
    res1 = client.get(
        "/api/v1/admin/dashboard-stats",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res1.status_code == 403

    res2 = client.get(
        "/api/v1/admin/students",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res2.status_code == 403

    res3 = client.get(
        "/api/v1/admin/results",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res3.status_code == 403
