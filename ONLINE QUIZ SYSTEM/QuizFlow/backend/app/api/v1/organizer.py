"""
Organizer (Teacher) Workspace Endpoints.
Provides personal dashboard statistics, quiz management, participant grading, and CSV export.
"""
from typing import List

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_db
from app.models.user import User, UserRole
from app.schemas.quiz import (
    AIGeneratedQuizResponse,
    AIGenerateQuizRequest,
    AIImportFileQuizRequest,
    OrganizerDashboardStats,
    QuizAdminResponse,
    QuizReportResponse,
)
from app.services.quiz_service import QuizService
from app.services.ai_generator_service import AIGeneratorService

router = APIRouter()


@router.get(
    "/dashboard-stats",
    response_model=OrganizerDashboardStats,
    summary="Get statistics for the logged-in organizer",
)
def get_organizer_stats(
    db: Session = Depends(get_db),
    current_organizer: User = Depends(get_current_organizer),
):
    """
    Returns real statistics for the teacher: quizzes created, drafts, published,
    total unique participants, attempt counts, and average score.
    """
    return QuizService.get_organizer_dashboard_stats(db, organizer_id=current_organizer.id)


@router.get(
    "/quizzes",
    response_model=List[QuizAdminResponse],
    summary="List all quizzes owned by the logged-in organizer",
)
def get_my_quizzes(
    db: Session = Depends(get_db),
    current_organizer: User = Depends(get_current_organizer),
):
    """
    Returns quizzes created by this teacher with participant count and draft/published status.
    """
    return QuizService.get_organizer_quizzes(db, organizer_id=current_organizer.id)


@router.get(
    "/quizzes/{quiz_id}/report",
    response_model=QuizReportResponse,
    summary="Get comprehensive attempt report for an owned quiz",
)
def get_quiz_report(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_organizer: User = Depends(get_current_organizer),
):
    """
    Returns participant roster, scores, pass/fail status, and question-level accuracy breakdown.
    """
    is_admin = current_organizer.role == UserRole.ADMIN.value
    return QuizService.get_quiz_report(db, quiz_id, user_id=current_organizer.id, is_admin=is_admin)


@router.get(
    "/quizzes/{quiz_id}/export-csv",
    summary="Export quiz attempt results as CSV",
)
def export_quiz_results_csv(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_organizer: User = Depends(get_current_organizer),
):
    """
    Streams CSV spreadsheet of all student attempts and grades for the quiz.
    """
    is_admin = current_organizer.role == UserRole.ADMIN.value
    csv_data = QuizService.export_quiz_csv(db, quiz_id, user_id=current_organizer.id, is_admin=is_admin)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=quizflow_results_quiz_{quiz_id}.csv"},
    )


@router.post(
    "/quizzes/{quiz_id}/release-results",
    response_model=QuizAdminResponse,
    summary="Release quiz results to participants",
)
def release_quiz_results(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_organizer: User = Depends(get_current_organizer),
):
    """
    Authorizes students to view their detailed score breakdowns and solutions.
    """
    is_admin = current_organizer.role == UserRole.ADMIN.value
    return QuizService.release_results(db, quiz_id, user_id=current_organizer.id, is_admin=is_admin)


@router.post(
    "/ai/generate-quiz",
    response_model=AIGeneratedQuizResponse,
    summary="Generate assessment quiz using AI prompt",
)
def generate_quiz_with_ai(
    req: AIGenerateQuizRequest,
    db: Session = Depends(get_db),
    current_organizer: User = Depends(get_current_organizer),
):
    """
    Generates a full quiz and questions using AI (Cloud or Local engine).
    If save_directly is True, creates the quiz and questions in the database.
    """
    generated = AIGeneratorService.generate_quiz_from_prompt(
        prompt=req.prompt,
        num_questions=req.num_questions,
        difficulty=req.difficulty,
        topic=req.topic,
    )

    quiz_id = None
    join_code = None
    if req.save_directly:
        saved_quiz = AIGeneratorService.save_quiz_to_database(
            db=db,
            quiz_data=generated,
            creator_id=current_organizer.id,
            is_public=True,
        )
        quiz_id = saved_quiz.id
        join_code = saved_quiz.join_code

    return AIGeneratedQuizResponse(
        title=generated["title"],
        description=generated.get("description"),
        subject=generated.get("subject", "General"),
        duration_minutes=generated.get("duration_minutes", 30),
        passing_percentage=generated.get("passing_percentage", 50),
        questions=generated["questions"],
        quiz_id=quiz_id,
        join_code=join_code,
        source=generated.get("source", "ai_generated"),
    )


@router.post(
    "/ai/import-file-quiz",
    response_model=AIGeneratedQuizResponse,
    summary="Create quiz automatically from an uploaded file (CSV, JSON, TXT, MD)",
)
def import_quiz_from_file(
    req: AIImportFileQuizRequest,
    db: Session = Depends(get_db),
    current_organizer: User = Depends(get_current_organizer),
):
    """
    Parses questions or notes from an uploaded file and synthesizes a quiz.
    If save_directly is True, saves to database immediately.
    """
    parsed = AIGeneratorService.parse_and_generate_from_file(
        file_content=req.file_content,
        filename=req.filename,
        num_questions=req.num_questions,
        difficulty=req.difficulty,
    )

    quiz_id = None
    join_code = None
    if req.save_directly:
        saved_quiz = AIGeneratorService.save_quiz_to_database(
            db=db,
            quiz_data=parsed,
            creator_id=current_organizer.id,
            is_public=True,
        )
        quiz_id = saved_quiz.id
        join_code = saved_quiz.join_code

    return AIGeneratedQuizResponse(
        title=parsed["title"],
        description=parsed.get("description"),
        subject=parsed.get("subject", "Imported"),
        duration_minutes=parsed.get("duration_minutes", 30),
        passing_percentage=parsed.get("passing_percentage", 50),
        questions=parsed["questions"],
        quiz_id=quiz_id,
        join_code=join_code,
        source=parsed.get("source", "file_imported"),
    )
