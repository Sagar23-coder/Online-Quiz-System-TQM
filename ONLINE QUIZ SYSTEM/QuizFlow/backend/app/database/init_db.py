"""
Database initialization, non-destructive schema migrations, and admin bootstrapping.
"""
import logging
import random
import string

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.database.session import Base, SessionLocal, engine
from app.models.user import User, UserRole

logger = logging.getLogger("quizflow.init_db")


def _generate_join_code() -> str:
    """Generate a clean, unambiguous 6-character uppercase join code."""
    chars = "".join(c for c in string.ascii_uppercase + string.digits if c not in "IO01")
    return "QF-" + "".join(random.choices(chars, k=4))


def apply_safe_migrations(db: Session) -> None:
    """
    Safely inspect and add missing columns to SQLite without recreating or dropping tables.
    Preserves all existing user records, quizzes, questions, and attempt data.
    """
    try:
        # 1. Quizzes table column inspection
        result = db.execute(text("PRAGMA table_info(quizzes)")).fetchall()
        existing_quiz_cols = {row[1] for row in result}

        new_quiz_cols = [
            ("subject", "VARCHAR(100) DEFAULT 'General'"),
            ("instructions", "TEXT"),
            ("join_code", "VARCHAR(16)"),
            ("is_public", "BOOLEAN DEFAULT 1 NOT NULL"),
            ("max_attempts", "INTEGER DEFAULT 1 NOT NULL"),
            ("release_results_immediately", "BOOLEAN DEFAULT 1 NOT NULL"),
            ("results_released", "BOOLEAN DEFAULT 1 NOT NULL"),
            ("start_time", "DATETIME"),
            ("end_time", "DATETIME"),
            ("is_disabled", "BOOLEAN DEFAULT 0 NOT NULL"),
        ]

        for col_name, col_type in new_quiz_cols:
            if col_name not in existing_quiz_cols:
                logger.info("Migrating schema: adding column quizzes.%s", col_name)
                db.execute(text(f"ALTER TABLE quizzes ADD COLUMN {col_name} {col_type}"))
                db.commit()

        # Questions table column inspection (topic, difficulty, learning_objective)
        result_q = db.execute(text("PRAGMA table_info(questions)")).fetchall()
        existing_question_cols = {row[1] for row in result_q}
        new_q_cols = [
            ("topic", "VARCHAR(100) DEFAULT 'General'"),
            ("difficulty", "VARCHAR(20) DEFAULT 'medium'"),
            ("learning_objective", "VARCHAR(255) DEFAULT ''"),
        ]
        for col_name, col_type in new_q_cols:
            if col_name not in existing_question_cols:
                logger.info("Migrating schema: adding column questions.%s", col_name)
                db.execute(text(f"ALTER TABLE questions ADD COLUMN {col_name} {col_type}"))
                db.commit()

        # 2. Assign unique join codes to any existing quizzes that lack one
        quizzes_without_code = db.execute(text("SELECT id FROM quizzes WHERE join_code IS NULL OR join_code = ''")).fetchall()
        for (q_id,) in quizzes_without_code:
            code = _generate_join_code()
            db.execute(text("UPDATE quizzes SET join_code = :code WHERE id = :qid"), {"code": code, "qid": q_id})
        if quizzes_without_code:
            db.commit()
            logger.info("Generated join codes for %d existing quizzes.", len(quizzes_without_code))

        # 3. Users role safety migration: support both 'student' and 'participant'
        # Convert legacy 'student' to 'participant' if desired, preserving data
        db.execute(text("UPDATE users SET role = 'participant' WHERE role = 'student'"))
        db.commit()

        logger.info("Schema migrations verified and safely applied.")
    except Exception as e:
        logger.warning("Safe migration check completed with notice: %s", e)
        db.rollback()


def init_db(db: Session = None) -> None:
    """Create all tables in the database if they do not exist, and apply safe migrations."""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        apply_safe_migrations(db)
        logger.info("Database tables verified/created successfully.")
    finally:
        if close_session:
            db.close()


def bootstrap_admin(
    email: str = None,
    password: str = None,
    full_name: str = None,
    db: Session = None,
) -> bool:
    """
    Securely bootstrap an initial administrator account if none exists.
    Can be run via CLI or startup hook.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        init_db(db)

        # Use environment settings if parameters not provided
        admin_email = email or settings.FIRST_SUPERUSER_EMAIL
        admin_password = password or settings.FIRST_SUPERUSER_PASSWORD
        admin_name = full_name or settings.FIRST_SUPERUSER_NAME

        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        if existing_admin:
            logger.info("An administrator account already exists. Bootstrap skipped.")
            return False

        if not admin_email or not admin_password:
            logger.warning(
                "Administrator bootstrap skipped: configure FIRST_SUPERUSER_EMAIL and "
                "FIRST_SUPERUSER_PASSWORD, or run `python -m app.cli create-admin`."
            )
            return False

        # Check if email is already taken
        user_by_email = db.query(User).filter(User.email == admin_email).first()
        if user_by_email:
            # Upgrade existing user to admin
            user_by_email.role = UserRole.ADMIN.value
            db.commit()
            logger.info("Upgraded existing user to admin role: %s", admin_email)
            return True

        admin_user = User(
            email=admin_email,
            full_name=admin_name,
            hashed_password=get_password_hash(admin_password),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        logger.info("Initial administrator account bootstrapped successfully: %s", admin_email)
        return True
    finally:
        if close_session:
            db.close()
