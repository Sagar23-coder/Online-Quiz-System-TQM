"""
Authentication and User Service with Audit Logging and Multi-Role Registration.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.rate_limit import auth_rate_limiter
from app.core.security import (
    create_access_token,
    get_password_hash,
    validate_password_complexity,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate, ip_address: Optional[str] = None) -> UserResponse:
        """Register a new user account with role validation (organizer or participant)."""
        normalized_email = user_in.email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )

        # Enforce password complexity policy
        is_valid_pw, pw_msg = validate_password_complexity(user_in.password)
        if not is_valid_pw:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pw_msg)

        # Enforce server-side validated role
        role_val = user_in.role or UserRole.PARTICIPANT.value
        if role_val not in (UserRole.ORGANIZER.value, UserRole.PARTICIPANT.value):
            role_val = UserRole.PARTICIPANT.value

        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            email=normalized_email,
            full_name=user_in.full_name.strip(),
            hashed_password=hashed_password,
            role=role_val,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Audit log event
        AuditService.log(
            db,
            action="AUTH_REGISTER",
            user_id=new_user.id,
            resource_type="user",
            resource_id=new_user.id,
            details={"email": new_user.email, "role": new_user.role, "full_name": new_user.full_name},
            ip_address=ip_address,
        )

        return UserResponse.model_validate(new_user)

    # Backward compatibility alias
    @staticmethod
    def register_student(db: Session, user_in: UserCreate, ip_address: Optional[str] = None) -> UserResponse:
        return AuthService.register_user(db, user_in, ip_address)

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin, ip_address: Optional[str] = None) -> Token:
        """Authenticate user by email and password and return a JWT bearer token with brute-force rate limiting."""
        normalized_email = login_data.email.strip().lower()

        # Check rate limiter
        is_limited, retry_sec = auth_rate_limiter.is_rate_limited(normalized_email)
        if not is_limited and ip_address:
            is_limited, retry_sec = auth_rate_limiter.is_rate_limited(ip_address)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Account temporarily locked. Please retry in {retry_sec} seconds.",
            )

        user = db.query(User).filter(User.email == normalized_email).first()

        if not user or not verify_password(login_data.password, user.hashed_password):
            auth_rate_limiter.record_attempt(normalized_email, success=False)
            if ip_address:
                auth_rate_limiter.record_attempt(ip_address, success=False)

            AuditService.log(
                db,
                action="AUTH_LOGIN_FAILED",
                user_id=user.id if user else None,
                resource_type="user",
                details={"email": normalized_email, "reason": "invalid_credentials"},
                ip_address=ip_address,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Login successful -> reset rate limiter
        auth_rate_limiter.record_attempt(normalized_email, success=True)
        if ip_address:
            auth_rate_limiter.record_attempt(ip_address, success=True)

        if not user.is_active:
            AuditService.log(
                db,
                action="AUTH_LOGIN_BLOCKED_SUSPENDED",
                user_id=user.id,
                resource_type="user",
                resource_id=user.id,
                details={"email": user.email, "reason": "account_suspended"},
                ip_address=ip_address,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been suspended or deactivated. Please contact an administrator.",
            )

        token = create_access_token(
            subject=str(user.id),
            role=user.role,
            email=user.email,
            name=user.full_name,
        )

        AuditService.log(
            db,
            action="AUTH_LOGIN_SUCCESS",
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            details={"email": user.email, "role": user.role},
            ip_address=ip_address,
        )

        return Token(
            access_token=token,
            token_type="bearer",
            role=user.role,
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user_profile(
        db: Session, user: User, profile_in: Any, ip_address: Optional[str] = None
    ) -> UserResponse:
        updated_fields = []
        if profile_in.full_name is not None and profile_in.full_name.strip():
            clean_name = profile_in.full_name.strip()
            if len(clean_name) < 2:
                raise HTTPException(status_code=400, detail="Full name must be at least 2 characters long.")
            user.full_name = clean_name
            updated_fields.append("full_name")

        if profile_in.new_password:
            if not profile_in.current_password:
                raise HTTPException(status_code=400, detail="Current password is required to change password.")
            if not verify_password(profile_in.current_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Current password verification failed.")
            if len(profile_in.new_password) < 6:
                raise HTTPException(status_code=400, detail="New password must be at least 6 characters long.")
            if profile_in.confirm_new_password and profile_in.new_password != profile_in.confirm_new_password:
                raise HTTPException(status_code=400, detail="New password and confirm password do not match.")
            user.hashed_password = get_password_hash(profile_in.new_password)
            updated_fields.append("password")

        db.commit()
        db.refresh(user)

        if updated_fields:
            AuditService.log(
                db,
                action="USER_PROFILE_UPDATE",
                user_id=user.id,
                resource_type="user",
                resource_id=user.id,
                details={"updated_fields": updated_fields},
                ip_address=ip_address,
            )

        return UserResponse.model_validate(user)
