"""Public import endpoint – receives a multipart file, validates, and launches extraction.
Provides preview and save endpoints for question import workflow.
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status, Body
from typing import List, Dict, Any

from app.services.question_import_service import QuestionImportService
from app.api.deps import get_current_organizer
from app.models.user import User

router = APIRouter()

# ------------------------------------------------------------------
# 1. Upload + preview – returns extracted question dicts (no DB write)
# ------------------------------------------------------------------
@router.post(
    "/import/{quiz_id}",
    summary="Upload a file to extract MCQs for a quiz",
    response_description="Preview of extracted questions",
    status_code=status.HTTP_200_OK,
)
async def upload_quiz_file(
    quiz_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_organizer),
) -> Dict[str, Any]:
    """Validate file, run extraction, and return a preview payload.
    The payload structure is a list of dicts each containing:
        - question_text
        - options (dict with keys A‑D)
        - correct_option (may be None)
        - marks (optional)
        - explanation (optional)
        - confidence (0‑1 float)
    """
    allowed_mimetypes = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/png",
        "image/jpeg",
        "image/webp",
    }
    if file.content_type not in allowed_mimetypes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # Store temporarily on disk
    import tempfile, shutil, os
    suffix = os.path.splitext(file.filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        with tmp as buffer:
            shutil.copyfileobj(file.file, buffer)
        tmp_path = tmp.name
    finally:
        await file.close()

    try:
        extracted = QuestionImportService.extract_only(quiz_id, tmp_path, user.id)
    except Exception as exc:
        os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(exc))

    os.remove(tmp_path)
    return {"extracted": extracted, "summary": {"count": len(extracted)}}

# ------------------------------------------------------------------
# 2. Save selected questions after teacher review
# ------------------------------------------------------------------
@router.post(
    "/import/{quiz_id}/save",
    summary="Persist selected extracted questions",
    response_description="Import result summary",
    status_code=status.HTTP_201_CREATED,
)
async def save_imported_questions(
    quiz_id: int,
    payload: List[Dict] = Body(...),
    user: User = Depends(get_current_organizer),
) -> Dict[str, Any]:
    """Accept preview payload (list of question dicts) and store them.
    Returns a summary of successes, skips, and errors.
    """
    try:
        summary = QuestionImportService.save_questions(quiz_id, payload, user.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return summary
