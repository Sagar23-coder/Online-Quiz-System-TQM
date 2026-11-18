"""
Database connection, engine configuration, and session management.
"""
import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger("quizflow.database")

# Configure SQLite or PostgreSQL engine appropriately
db_url = settings.SQLALCHEMY_DATABASE_URL
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and safely closes it upon exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
