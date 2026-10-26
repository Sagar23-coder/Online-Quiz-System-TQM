"""
Quiz Management Endpoints for Participants, Organizers, and Administrators.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_admin,
    get_current_organizer,
    get_current_user,
    get_db,
    get_optional_current_user,
)
from app.models.user import User, UserRole
from app.schemas.quiz import (
    JoinCodeRequest,
    QuizAdminResponse,
    QuizCreate,
    QuizDetailStudentResponse,
    QuizStudentResponse,
    QuizUpdate,
)
from app.services.quiz_service import QuizService

router = APIRouter()


@router.get(
    "",
    response_model=List[QuizStudentResponse],
    summary="List all public published quizzes for participants",
)
def list_published_quizzes(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Participant/Public endpoint: Returns only active, published quizzes marked for public discovery.
    """
    user_id = current_user.id if current_user else None
    return QuizService.get_student_quizzes(db, student_id=user_id)


@router.post(
    "/join-by-code",
    response_model=QuizStudentResponse,
    summary="Discover and join a private or public quiz using an Organizer's Join Code",
)
def join_quiz_by_code(
    payload: JoinCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validates the join code, verifies publication status and time windows,
    and returns quiz details for the participant to begin.
    """
    return QuizService.get_quiz_by_join_code(db, payload.join_code, student_id=current_user.id)


@router.get(
    "/by-code/{join_code}",
    response_model=QuizStudentResponse,
    summary="Get quiz details by join code",
)
def get_quiz_by_code(
    join_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lookup quiz by join code.
    """
    return QuizService.get_quiz_by_join_code(db, join_code, student_id=current_user.id)


@router.get(
    "/admin/all",
    response_model=List[QuizAdminResponse],
    summary="List all platform quizzes (Admin only)",
)
def list_admin_quizzes(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Administrator endpoint: Returns all quizzes (draft, published, disabled) across all organizers.
    """
    return QuizService.get_admin_quizzes(db)


@router.post(
    "",
    response_model=QuizAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new quiz (Organizer or Admin)",
)
def create_quiz(
    quiz_in: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    """
    Creates a new quiz in draft mode with an automatically generated secure join code.
    """
    return QuizService.create_quiz(db, quiz_in, creator_id=current_user.id)


@router.get(
    "/{quiz_id}",
    response_model=QuizDetailStudentResponse,
    summary="Get quiz instructions/details",
)
def get_quiz_details(quiz_id: int, db: Session = Depends(get_db)):
    """
    Returns basic quiz metadata, duration, passing percentage, and instructions.
    """
    quizzes = QuizService.get_student_quizzes(db)
    for q in quizzes:
        if q.id == quiz_id:
            return q

    # Check if admin/organizer is requesting a draft
    admin_quizzes = QuizService.get_admin_quizzes(db)
    for q in admin_quizzes:
        if q.id == quiz_id:
            return QuizDetailStudentResponse(
                id=q.id,
                title=q.title,
                description=q.description,
                instructions=q.instructions,
                duration_minutes=q.duration_minutes,
                passing_percentage=q.passing_percentage,
                total_marks=q.total_marks,
                question_count=q.question_count,
                join_code=q.join_code,
                is_public=q.is_public,
                creator_name=q.creator_name,
                max_attempts=q.max_attempts,
                results_released=q.results_released,
            )

    raise HTTPException(status_code=404, detail="Quiz not found")


@router.put(
    "/{quiz_id}",
    response_model=QuizAdminResponse,
    summary="Update quiz settings (Organizer or Admin)",
)
def update_quiz(
    quiz_id: int,
    quiz_in: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    """
    Updates quiz title, description, schedule, and attempt rules.
    Enforces that organizers can only edit their own quizzes.
    """
    is_admin = current_user.role == UserRole.ADMIN.value
    return QuizService.update_quiz(db, quiz_id, quiz_in, user_id=current_user.id, is_admin=is_admin)


@router.delete(
    "/{quiz_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a quiz (Organizer or Admin)",
)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    """
    Deletes a quiz. Organizers can only delete their own quizzes.
    """
    is_admin = current_user.role == UserRole.ADMIN.value
    QuizService.delete_quiz(db, quiz_id, user_id=current_user.id, is_admin=is_admin)
    return {"message": "Quiz deleted successfully", "quiz_id": quiz_id}


@router.post(
    "/{quiz_id}/publish",
    response_model=QuizAdminResponse,
    summary="Publish a quiz (Organizer or Admin)",
)
def publish_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    """
    Publishes a quiz if it has valid questions.
    """
    is_admin = current_user.role == UserRole.ADMIN.value
    return QuizService.publish_quiz(db, quiz_id, user_id=current_user.id, is_admin=is_admin)


@router.post(
    "/{quiz_id}/unpublish",
    response_model=QuizAdminResponse,
    summary="Unpublish a quiz (Organizer or Admin)",
)
def unpublish_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    """
    Unpublishes a quiz, returning it to draft mode.
    """
    is_admin = current_user.role == UserRole.ADMIN.value
    return QuizService.unpublish_quiz(db, quiz_id, user_id=current_user.id, is_admin=is_admin)
