"""
API V1 Router Aggregation.
"""
from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.attempts import router as attempts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.organizer import router as organizer_router
from app.api.v1.questions import router as questions_router
from app.api.v1.quizzes import router as quizzes_router

api_router = APIRouter()

# Health
api_router.include_router(health_router, tags=["Health"])

# Authentication
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Quizzes
api_router.include_router(quizzes_router, prefix="/quizzes", tags=["Quizzes"])

# Organizer Workspace
api_router.include_router(organizer_router, prefix="/organizer", tags=["Organizer Workspace"])

# Questions
api_router.include_router(questions_router, tags=["Questions"])

# Attempts and Grading
api_router.include_router(attempts_router, prefix="/attempts", tags=["Attempts"])

# Admin Statistics and Moderation
api_router.include_router(admin_router, prefix="/admin", tags=["Admin Management"])
