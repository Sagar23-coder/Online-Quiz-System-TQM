"""
Pytest configuration and fixtures.
Configures isolated test database and FastAPI TestClient.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_FILE = "./test_quizflow.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "test_secret_key_at_least_32_characters_long_for_tests"
os.environ["ENVIRONMENT"] = "testing"

from app.core.security import get_password_hash
from app.database.session import Base, get_db
from app.main import app
from app.models.user import User, UserRole

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database():
    """Ensure clean start and remove test db after entire session."""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass
    yield
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest.fixture(scope="function")
def db_session():
    """Recreate tables per test function for complete test isolation."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Fixture providing a test admin user."""
    admin = User(
        email="test_admin@quizflow.local",
        full_name="Test Administrator",
        hashed_password=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    """Fixture providing a valid admin JWT token."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "AdminPass123!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="function")
def student_user(db_session):
    """Fixture providing a test student user."""
    student = User(
        email="test_student@quizflow.local",
        full_name="Test Student",
        hashed_password=get_password_hash("StudentPass123!"),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


@pytest.fixture(scope="function")
def student_token(client, student_user):
    """Fixture providing a valid student JWT token."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": student_user.email, "password": "StudentPass123!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]
