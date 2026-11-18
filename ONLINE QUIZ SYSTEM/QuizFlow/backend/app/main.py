"""
QuizFlow FastAPI Main Application.
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.database.init_db import bootstrap_admin, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("quizflow.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables are created
    logger.info("Initializing database...")
    init_db()
    # Bootstrap default administrator if configured and not present
    bootstrap_admin()
    logger.info("QuizFlow backend initialized successfully.")
    yield
    # Shutdown
    logger.info("QuizFlow backend shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Professional Online Quiz & Assessment Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
origins = settings.BACKEND_CORS_ORIGINS
if "*" in origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Security Headers and Request Tracing Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    import secrets
    correlation_id = request.headers.get("X-Request-ID") or secrets.token_hex(8)
    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        "%s %s -> %d (%.2fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration * 1000,
    )
    return response


# Validation Error Handler

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0]["msg"] if errors else "Validation failed"
    # Convert errors to safely serializable list
    safe_errors = []
    for err in errors:
        safe_err = {
            "type": err.get("type", "value_error"),
            "loc": err.get("loc", []),
            "msg": err.get("msg", ""),
        }
        safe_errors.append(safe_err)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": first_error, "errors": safe_errors},
    )


# Top-level root & health endpoints
@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["Health"])
def direct_health():
    from sqlalchemy import text
    from app.database.session import SessionLocal
    db = SessionLocal()
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    finally:
        db.close()

    return {
        "status": "online" if db_status == "healthy" else "degraded",
        "database": db_status,
        "app": settings.PROJECT_NAME,
    }


@app.get("/health/ready", tags=["Health"])
def readiness_probe():
    """Readiness probe for cloud orchestrators (Render, Kubernetes). Checks database pool latency."""
    import time
    from sqlalchemy import text
    from app.database.session import SessionLocal
    start = time.time()
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start) * 1000, 2)
        return {
            "status": "ready",
            "database_latency_ms": latency_ms,
            "app": settings.PROJECT_NAME,
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "error": str(e)},
        )
    finally:
        db.close()


# Include API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


# Public Student Quiz Web Interface (Direct link access without login)
@app.get("/quiz/{share_token}", response_class=HTMLResponse, tags=["Public Quiz Web"])
def public_quiz_web_page(share_token: str):
    from pathlib import Path
    template_path = Path(__file__).resolve().parent / "templates" / "public_quiz.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h3>QuizFlow Student Assessment Portal</h3><p>Loading assessment...</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
