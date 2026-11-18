"""
QuizFlow Core Application Settings.
Supports loading from environment variables, .env file, and defaults.
"""
import json
import os
import secrets
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Find .env relative to this file or working directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


def get_network_ip() -> str:
    """Get the machine's primary local network IP address."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            import socket
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "QuizFlow")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Public Quiz Web Base URL for Shareable Student Links (Accessible on Any System)
    _public_base_url_env: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

    @property
    def PUBLIC_BASE_URL(self) -> str:
        if self._public_base_url_env and "localhost" not in self._public_base_url_env and "127.0.0.1" not in self._public_base_url_env:
            return self._public_base_url_env
        port = os.getenv("PORT", "8000")
        return f"http://{get_network_ip()}:{port}"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'quizflow.db'}")

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """
        Normalize DATABASE_URL for SQLAlchemy 2.0.
        Converts 'postgres://' or 'postgresql://' prefixes to 'postgresql+psycopg2://'
        for PostgreSQL connections from Render/Neon/Supabase.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    # Bootstrap Admin
    FIRST_SUPERUSER_EMAIL: str = os.getenv("FIRST_SUPERUSER_EMAIL", "")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "")
    FIRST_SUPERUSER_NAME: str = os.getenv("FIRST_SUPERUSER_NAME", "QuizFlow Administrator")

    # CORS
    _cors_raw: str = os.getenv(
        "BACKEND_CORS_ORIGINS",
        '["http://localhost:3000","http://localhost:8081","http://localhost:19006","http://localhost:8000","*"]',
    )

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        try:
            origins = json.loads(self._cors_raw)
            if isinstance(origins, list):
                return origins
            return [str(origins)]
        except Exception:
            return ["*"]


settings = Settings()
