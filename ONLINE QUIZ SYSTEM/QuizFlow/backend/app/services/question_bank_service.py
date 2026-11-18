"""
Question Bank Service for QuizFlow 2.0.
Strictly enforces teacher multi-tenancy: teachers can only manage and view their own question banks.
"""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.question_bank import QuestionBank, QuestionBankItem
from app.models.question import Question
from app.models.quiz import Quiz
from app.schemas.question_bank import (
    QuestionBankCreate,
    QuestionBankUpdate,
    QuestionBankItemCreate,
    QuestionBankItemUpdate,
    QuestionBankResponse,
    QuestionBankItemResponse,
)
from app.services.audit_service import AuditService


class QuestionBankService:
    @staticmethod
    def get_teacher_banks(db: Session, teacher_id: int) -> List[QuestionBankResponse]:
        banks = (
            db.query(QuestionBank)
            .filter(QuestionBank.teacher_id == teacher_id)
            .order_by(QuestionBank.created_at.desc())
            .all()
        )
        responses = []
        for b in banks:
            count = db.query(QuestionBankItem).filter(QuestionBankItem.bank_id == b.id).count()
            resp = QuestionBankResponse.model_validate(b)
            resp.item_count = count
            responses.append(resp)
        return responses

    @staticmethod
    def create_bank(db: Session, teacher_id: int, bank_in: QuestionBankCreate) -> QuestionBankResponse:
        bank = QuestionBank(
            teacher_id=teacher_id,
            title=bank_in.title.strip(),
            description=bank_in.description.strip() if bank_in.description else None,
            subject=bank_in.subject.strip() if bank_in.subject else "General",
            grade_level=bank_in.grade_level.strip() if bank_in.grade_level else None,
            topic=bank_in.topic.strip() if bank_in.topic else None,
            difficulty=bank_in.difficulty,
            tags=bank_in.tags.strip() if bank_in.tags else None,
        )
        db.add(bank)
        db.commit()
        db.refresh(bank)

        AuditService.log(
            db,
            action="QUESTION_BANK_CREATE",
            user_id=teacher_id,
            resource_type="question_bank",
            resource_id=bank.id,
            details={"title": bank.title},
        )
        resp = QuestionBankResponse.model_validate(bank)
        resp.item_count = 0
        return resp

    @staticmethod
    def get_bank_details(db: Session, bank_id: int, teacher_id: int) -> QuestionBankResponse:
        bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
        if not bank:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question bank not found.")
        if bank.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to another teacher's question bank.")

        items = db.query(QuestionBankItem).filter(QuestionBankItem.bank_id == bank_id).all()
        resp = QuestionBankResponse.model_validate(bank)
        resp.item_count = len(items)
        resp.items = [QuestionBankItemResponse.model_validate(item) for item in items]
        return resp

    @staticmethod
    def update_bank(db: Session, bank_id: int, teacher_id: int, bank_in: QuestionBankUpdate) -> QuestionBankResponse:
        bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
        if not bank:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question bank not found.")
        if bank.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        if bank_in.title is not None:
            bank.title = bank_in.title.strip()
        if bank_in.description is not None:
            bank.description = bank_in.description.strip() if bank_in.description else None
        if bank_in.subject is not None:
            bank.subject = bank_in.subject.strip()
        if bank_in.grade_level is not None:
            bank.grade_level = bank_in.grade_level.strip()
        if bank_in.topic is not None:
            bank.topic = bank_in.topic.strip()
        if bank_in.difficulty is not None:
            bank.difficulty = bank_in.difficulty
        if bank_in.tags is not None:
            bank.tags = bank_in.tags.strip()

        db.commit()
        db.refresh(bank)
        count = db.query(QuestionBankItem).filter(QuestionBankItem.bank_id == bank_id).count()
        resp = QuestionBankResponse.model_validate(bank)
        resp.item_count = count
        return resp

    @staticmethod
    def delete_bank(db: Session, bank_id: int, teacher_id: int) -> bool:
        bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
        if not bank:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question bank not found.")
        if bank.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        db.delete(bank)
        db.commit()
        return True

    @staticmethod
    def add_item_to_bank(
        db: Session, bank_id: int, teacher_id: int, item_in: QuestionBankItemCreate
    ) -> QuestionBankItemResponse:
        bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
        if not bank:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question bank not found.")
        if bank.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        item = QuestionBankItem(
            bank_id=bank_id,
            question_text=item_in.question_text.strip(),
            question_type=item_in.question_type,
            option_a=item_in.option_a.strip() if item_in.option_a else "",
            option_b=item_in.option_b.strip() if item_in.option_b else "",
            option_c=item_in.option_c.strip() if item_in.option_c else "",
            option_d=item_in.option_d.strip() if item_in.option_d else "",
            correct_option=item_in.correct_option.strip().upper(),
            correct_answers=item_in.correct_answers,
            marks=item_in.marks,
            explanation=item_in.explanation.strip() if item_in.explanation else None,
            cognitive_level=item_in.cognitive_level,
            difficulty=item_in.difficulty,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return QuestionBankItemResponse.model_validate(item)

    @staticmethod
    def import_items_to_quiz(
        db: Session, bank_id: int, quiz_id: int, teacher_id: int, item_ids: List[int]
    ) -> int:
        """Imports selected questions from a teacher's Question Bank into an owned quiz."""
        bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
        if not bank or bank.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this question bank.")

        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz or quiz.created_by_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to destination quiz.")

        items = (
            db.query(QuestionBankItem)
            .filter(QuestionBankItem.bank_id == bank_id, QuestionBankItem.id.in_(item_ids))
            .all()
        )

        max_order = db.query(func.max(Question.order_index)).filter(Question.quiz_id == quiz.id).scalar() or 0
        added_count = 0

        for itm in items:
            max_order += 1
            new_q = Question(
                quiz_id=quiz.id,
                question_text=itm.question_text,
                option_a=itm.option_a or "",
                option_b=itm.option_b or "",
                option_c=itm.option_c or "",
                option_d=itm.option_d or "",
                correct_option=itm.correct_option,
                marks=itm.marks,
                explanation=itm.explanation,
                order_index=max_order,
                topic=bank.topic or bank.subject,
                difficulty=itm.difficulty,
            )
            db.add(new_q)
            added_count += 1

        db.flush()
        quiz.total_marks = db.query(func.sum(Question.marks)).filter(Question.quiz_id == quiz.id).scalar() or 0
        db.commit()

        AuditService.log(
            db,
            action="QUESTION_BANK_IMPORT_TO_QUIZ",
            user_id=teacher_id,
            resource_type="quiz",
            resource_id=quiz.id,
            details={"bank_id": bank.id, "imported_count": added_count},
        )
        return added_count
