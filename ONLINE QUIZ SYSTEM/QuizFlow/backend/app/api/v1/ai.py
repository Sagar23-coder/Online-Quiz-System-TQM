"""
AI Quality and Translation Endpoints for QuizFlow 2.0.
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_organizer
from app.models.user import User
from app.services.ai_quality_service import AIQualityService

router = APIRouter()


class QuestionQualityCheckRequest(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: Optional[str] = None


class QuestionTranslateRequest(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    explanation: Optional[str] = None
    target_lang: str = "hi"


@router.post(
    "/validate-question",
    summary="Pedagogical quality audit for assessment questions",
)
def audit_question_quality(
    req: QuestionQualityCheckRequest,
    current_user: User = Depends(get_current_organizer),
):
    """
    Evaluates distractor distinctness, length bias, negative phrasing, and cognitive clarity.
    Returns quality score 0-100 and actionable recommendations.
    """
    return AIQualityService.audit_question_quality(
        question_text=req.question_text,
        option_a=req.option_a,
        option_b=req.option_b,
        option_c=req.option_c,
        option_d=req.option_d,
        correct_option=req.correct_option,
        explanation=req.explanation,
    )


@router.post(
    "/translate-question",
    summary="Translate question and choices to Hindi/English",
)
def translate_question(
    req: QuestionTranslateRequest,
    current_user: User = Depends(get_current_organizer),
):
    """
    Bilingual support endpoint for Hindi/English localization.
    """
    return AIQualityService.translate_question_bilingual(
        question_text=req.question_text,
        option_a=req.option_a,
        option_b=req.option_b,
        option_c=req.option_c,
        option_d=req.option_d,
        explanation=req.explanation,
        target_lang=req.target_lang,
    )
