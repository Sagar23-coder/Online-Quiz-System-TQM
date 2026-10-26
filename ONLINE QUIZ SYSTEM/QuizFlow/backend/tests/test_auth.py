"""
Tests for user registration, authentication, and role assignment.
"""


def test_student_registration_success(client):
    payload = {
        "email": "newstudent@example.com",
        "full_name": "New Student",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newstudent@example.com"
    assert data["full_name"] == "New Student"
    assert data["role"] in ("participant", "student")
    assert "hashed_password" not in data


def test_registration_password_mismatch(client):
    payload = {
        "email": "mismatch@example.com",
        "full_name": "Mismatch Test",
        "password": "Password123!",
        "confirm_password": "DifferentPassword456!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_registration_duplicate_email(client, student_user):
    payload = {
        "email": student_user.email,
        "full_name": "Duplicate Tester",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client, student_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": student_user.email, "password": "StudentPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "student"
    assert data["user"]["email"] == student_user.email


def test_login_invalid_password(client, student_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": student_user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "SomePassword123!"},
    )
    assert response.status_code == 401


def test_get_me_authenticated(client, student_token, student_user):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_user.id
    assert data["email"] == student_user.email


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

