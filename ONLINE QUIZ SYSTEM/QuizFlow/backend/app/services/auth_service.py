"""
Authentication and User Service with Audit Logging and Multi-Role Registration.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_password_hash,
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
        """Authenticate user by email and password and return a JWT bearer token."""
        normalized_email = login_data.email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()

        if not user or not verify_password(login_data.password, user.hashed_password):
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
