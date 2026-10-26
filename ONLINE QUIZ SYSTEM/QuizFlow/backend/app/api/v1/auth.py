"""
Authentication Endpoints: Multi-Role Registration, Login, Profile.
"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account (Organizer or Participant)",
)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    Public registration endpoint. Allows selecting between 'organizer' and 'participant'.
    Admin accounts cannot be registered publicly.
    """
    client_ip = request.client.host if request.client else None
    return AuthService.register_user(db, user_in, ip_address=client_ip)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive JWT token",
)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Authenticates Admin, Organizer, or Participant.
    Returns access_token, user profile, and role for automated UI routing.
    """
    client_ip = request.client.host if request.client else None
    return AuthService.authenticate_user(db, login_data, ip_address=client_ip)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user's profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns profile information for the currently authenticated user.
    """
    return UserResponse.model_validate(current_user)
