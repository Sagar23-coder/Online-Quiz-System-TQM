"""
Question Bank API Endpoints for Teachers (Organizers).
Provides reusable question repository management, multi-taxonomy filtering, and direct quiz imports.
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_db
from app.models.user import User
from app.schemas.question_bank import (
    QuestionBankCreate,
    QuestionBankUpdate,
    QuestionBankItemCreate,
    QuestionBankItemUpdate,
    QuestionBankResponse,
    QuestionBankItemResponse,
    ImportFromBankRequest,
)
from app.services.question_bank_service import QuestionBankService

router = APIRouter()


@router.get(
    "",
    response_model=List[QuestionBankResponse],
    summary="List all Question Banks owned by the authenticated teacher",
)
def list_question_banks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return QuestionBankService.get_teacher_banks(db, teacher_id=current_user.id)


@router.post(
    "",
    response_model=QuestionBankResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Question Bank",
)
def create_question_bank(
    bank_in: QuestionBankCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return QuestionBankService.create_bank(db, teacher_id=current_user.id, bank_in=bank_in)


@router.get(
    "/{bank_id}",
    response_model=QuestionBankResponse,
    summary="Get Question Bank details with all questions",
)
def get_question_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return QuestionBankService.get_bank_details(db, bank_id=bank_id, teacher_id=current_user.id)


@router.put(
    "/{bank_id}",
    response_model=QuestionBankResponse,
    summary="Update Question Bank metadata",
)
def update_question_bank(
    bank_id: int,
    bank_in: QuestionBankUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return QuestionBankService.update_bank(db, bank_id=bank_id, teacher_id=current_user.id, bank_in=bank_in)


@router.delete(
    "/{bank_id}",
    summary="Delete a Question Bank",
)
def delete_question_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    QuestionBankService.delete_bank(db, bank_id=bank_id, teacher_id=current_user.id)
    return {"message": "Question bank deleted successfully", "bank_id": bank_id}


@router.post(
    "/{bank_id}/questions",
    response_model=QuestionBankItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a question to a Question Bank",
)
def add_question_to_bank(
    bank_id: int,
    item_in: QuestionBankItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    return QuestionBankService.add_item_to_bank(db, bank_id=bank_id, teacher_id=current_user.id, item_in=item_in)


@router.post(
    "/{bank_id}/import-to-quiz/{quiz_id}",
    summary="Import selected questions from Question Bank directly into an owned Quiz",
)
def import_questions_to_quiz(
    bank_id: int,
    quiz_id: int,
    payload: ImportFromBankRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    count = QuestionBankService.import_items_to_quiz(
        db, bank_id=bank_id, quiz_id=quiz_id, teacher_id=current_user.id, item_ids=payload.item_ids
    )
    return {"message": f"Successfully imported {count} question(s) into quiz.", "imported_count": count}
