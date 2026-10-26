"""
Security utilities: Password hashing, verification, and JWT operations.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from .config import settings

# Attempt Argon2 hashing, with PBKDF2-SHA256 fallback for portability
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerificationError, VerifyMismatchError
    _hasher = PasswordHasher()
    _USE_ARGON2 = True
except ImportError:
    _hasher = None
    _USE_ARGON2 = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored hash."""
    if not plain_password or not hashed_password:
        return False

    if hashed_password.startswith("$argon2"):
        if _USE_ARGON2:
            try:
                return _hasher.verify(hashed_password, plain_password)
            except (VerifyMismatchError, VerificationError):
                return False
            except Exception:
                return False
        return False

    # PBKDF2 fallback format: pbkdf2_sha256$iterations$salt$hash
    if hashed_password.startswith("pbkdf2_sha256$"):
        import hashlib
        try:
            _, iter_str, salt, target_hash = hashed_password.split("$", 3)
            iterations = int(iter_str)
            computed = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            ).hex()
            return computed == target_hash
        except Exception:
            return False

    return False


def get_password_hash(password: str) -> str:
    """Generate a secure cryptographic hash for the given password."""
    if _USE_ARGON2:
        return _hasher.hash(password)

    import hashlib
    import secrets
    salt = secrets.token_hex(16)
    iterations = 100_000
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${hashed}"


def create_access_token(
    subject: str,
    role: str,
    email: str,
    name: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token containing subject and user claims."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "email": email,
        "name": name,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except (jwt.PyJWTError, Exception):
        return None
