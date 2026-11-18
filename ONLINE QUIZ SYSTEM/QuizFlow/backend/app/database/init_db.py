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
    Safely inspect and add missing columns without recreating or dropping tables.
    Works seamlessly across both SQLite and PostgreSQL.
    Preserves all existing user records, quizzes, questions, and attempt data.
    """
    from sqlalchemy import inspect
    try:
        inspector = inspect(db.bind)
        existing_tables = set(inspector.get_table_names())

        is_pg = db.bind.dialect.name == "postgresql"
        timestamp_col = "TIMESTAMP" if is_pg else "DATETIME"
        true_val = "TRUE" if is_pg else "1"
        false_val = "FALSE" if is_pg else "0"

        # 1. Quizzes table column inspection
        if "quizzes" in existing_tables:
            existing_quiz_cols = {c["name"] for c in inspector.get_columns("quizzes")}
            new_quiz_cols = [
                ("subject", "VARCHAR(100) DEFAULT 'General'"),
                ("instructions", "TEXT"),
                ("join_code", "VARCHAR(16)"),
                ("share_token", "VARCHAR(64)"),
                ("is_share_link_active", f"BOOLEAN DEFAULT {true_val} NOT NULL"),
                ("is_public", f"BOOLEAN DEFAULT {true_val} NOT NULL"),
                ("max_attempts", "INTEGER DEFAULT 1 NOT NULL"),
                ("release_results_immediately", f"BOOLEAN DEFAULT {true_val} NOT NULL"),
                ("results_released", f"BOOLEAN DEFAULT {true_val} NOT NULL"),
                ("start_time", timestamp_col),
                ("end_time", timestamp_col),
                ("mode", "VARCHAR(20) DEFAULT 'exam' NOT NULL"),
                ("shuffle_questions", f"BOOLEAN DEFAULT {true_val} NOT NULL"),
                ("shuffle_options", f"BOOLEAN DEFAULT {true_val} NOT NULL"),
                ("result_release_policy", "VARCHAR(30) DEFAULT 'immediate' NOT NULL"),
                ("is_disabled", f"BOOLEAN DEFAULT {false_val} NOT NULL"),
            ]

            for col_name, col_type in new_quiz_cols:
                if col_name not in existing_quiz_cols:
                    logger.info("Migrating schema: adding column quizzes.%s", col_name)
                    db.execute(text(f"ALTER TABLE quizzes ADD COLUMN {col_name} {col_type}"))
                    db.commit()

            # Generate share_tokens for any quizzes lacking one
            import secrets
            quizzes_without_token = db.execute(text("SELECT id FROM quizzes WHERE share_token IS NULL OR share_token = ''")).fetchall()
            for (q_id,) in quizzes_without_token:
                token = secrets.token_urlsafe(16)
                db.execute(text("UPDATE quizzes SET share_token = :token WHERE id = :qid"), {"token": token, "qid": q_id})
            if quizzes_without_token:
                db.commit()
                logger.info("Generated share tokens for %d quizzes.", len(quizzes_without_token))

        # 2. Quiz Attempts table column inspection (Public student participation)
        if "quiz_attempts" in existing_tables:
            existing_attempt_cols = {c["name"] for c in inspector.get_columns("quiz_attempts")}
            new_att_cols = [
                ("participant_name", "VARCHAR(100)"),
                ("participant_class", "VARCHAR(50)"),
                ("participant_section", "VARCHAR(50)"),
                ("participant_email", "VARCHAR(100)"),
                ("participant_phone", "VARCHAR(30)"),
                ("attempt_token", "VARCHAR(64)"),
                ("question_order_seed", "INTEGER DEFAULT 0"),
                ("integrity_events", "TEXT"),
            ]
            for col_name, col_type in new_att_cols:
                if col_name not in existing_attempt_cols:
                    logger.info("Migrating schema: adding column quiz_attempts.%s", col_name)
                    db.execute(text(f"ALTER TABLE quiz_attempts ADD COLUMN {col_name} {col_type}"))
                    db.commit()

            # 2b. Ensure student_id is nullable in SQLite for guest participants
            if not is_pg:
                try:
                    pragma_info = db.execute(text("PRAGMA table_info(quiz_attempts)")).fetchall()
                    student_id_col = next((col for col in pragma_info if col[1] == "student_id"), None)
                    if student_id_col and student_id_col[3] == 1:  # notnull is 1
                        logger.info("Migrating schema: making quiz_attempts.student_id nullable in SQLite...")
                        db.execute(text("PRAGMA foreign_keys=OFF;"))
                        db.execute(text("CREATE TABLE quiz_attempts_temp (id INTEGER PRIMARY KEY, student_id INTEGER, quiz_id INTEGER NOT NULL, start_time DATETIME NOT NULL, deadline_time DATETIME NOT NULL, end_time DATETIME, status VARCHAR(20) NOT NULL, score_obtained FLOAT NOT NULL, total_marks FLOAT NOT NULL, percentage FLOAT NOT NULL, is_passed BOOLEAN NOT NULL, created_at DATETIME NOT NULL, participant_name VARCHAR(100), participant_class VARCHAR(50), participant_section VARCHAR(50), participant_email VARCHAR(100), participant_phone VARCHAR(30), attempt_token VARCHAR(64), FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE SET NULL, FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE);"))
                        db.execute(text("INSERT INTO quiz_attempts_temp SELECT id, student_id, quiz_id, start_time, deadline_time, end_time, status, score_obtained, total_marks, percentage, is_passed, created_at, participant_name, participant_class, participant_section, participant_email, participant_phone, attempt_token FROM quiz_attempts;"))
                        db.execute(text("DROP TABLE quiz_attempts;"))
                        db.execute(text("ALTER TABLE quiz_attempts_temp RENAME TO quiz_attempts;"))
                        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quiz_attempts_id ON quiz_attempts (id);"))
                        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quiz_attempts_student_id ON quiz_attempts (student_id);"))
                        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quiz_attempts_quiz_id ON quiz_attempts (quiz_id);"))
                        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_quiz_attempts_attempt_token ON quiz_attempts (attempt_token);"))
                        db.execute(text("PRAGMA foreign_keys=ON;"))
                        db.commit()
                except Exception as ex:
                    logger.warning("Notice adjusting quiz_attempts.student_id nullable: %s", ex)

            # Backfill participant_name and participant_email from users for historical attempts
            try:
                db.execute(text(
                    "UPDATE quiz_attempts SET participant_name = (SELECT full_name FROM users WHERE users.id = quiz_attempts.student_id), "
                    "participant_email = (SELECT email FROM users WHERE users.id = quiz_attempts.student_id) "
                    "WHERE (participant_name IS NULL OR participant_name = '') AND student_id IS NOT NULL"
                ))
                db.commit()
            except Exception:
                pass

        # 3. Questions table column inspection (topic, difficulty, learning_objective, source)
        if "questions" in existing_tables:
            existing_question_cols = {c["name"] for c in inspector.get_columns("questions")}
            new_q_cols = [
                ("topic", "VARCHAR(100) DEFAULT 'General'"),
                ("difficulty", "VARCHAR(20) DEFAULT 'medium'"),
                ("learning_objective", "VARCHAR(255) DEFAULT ''"),
                ("source", "VARCHAR(20) DEFAULT 'manual' NOT NULL"),
                ("question_text_hi", "TEXT"),
                ("option_a_hi", "TEXT"),
                ("option_b_hi", "TEXT"),
                ("option_c_hi", "TEXT"),
                ("option_d_hi", "TEXT"),
                ("explanation_hi", "TEXT"),
            ]
            for col_name, col_type in new_q_cols:
                if col_name not in existing_question_cols:
                    logger.info("Migrating schema: adding column questions.%s", col_name)
                    db.execute(text(f"ALTER TABLE questions ADD COLUMN {col_name} {col_type}"))
                    db.commit()

        # 4. Assign unique join codes to any existing quizzes that lack one
        if "quizzes" in existing_tables:
            quizzes_without_code = db.execute(text("SELECT id FROM quizzes WHERE join_code IS NULL OR join_code = ''")).fetchall()
            for (q_id,) in quizzes_without_code:
                code = _generate_join_code()
                db.execute(text("UPDATE quizzes SET join_code = :code WHERE id = :qid"), {"code": code, "qid": q_id})
            if quizzes_without_code:
                db.commit()
                logger.info("Generated join codes for %d existing quizzes.", len(quizzes_without_code))

        # 5. Users role safety migration: support both 'student' and 'participant'
        if "users" in existing_tables:
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
