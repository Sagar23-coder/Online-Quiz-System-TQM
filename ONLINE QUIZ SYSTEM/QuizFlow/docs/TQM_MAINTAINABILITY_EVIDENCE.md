# QUIZFLOW 2.0 — TQM SOFTWARE MAINTAINABILITY EVIDENCE SPECIFICATION

This document provides formal evidence for the five Total Quality Management (TQM) Maintainability Requirements specified for QuizFlow 2.0.

---

## 1. Modular Structure

### Objective
High cohesion and low coupling across presentation, business domain, API routing, data persistence, and background jobs. Monolithic single-file architectures are strictly forbidden.

### Source Code Evidence
- **API Routing Layer (`backend/app/api/v1/`)**:
  - `auth.py`: User registration, JWT login, profile editing, and password update.
  - `quizzes.py`: Quiz CRUD, publishing, link generation, code discovery.
  - `questions.py`: Question CRUD, options management, ordering.
  - `attempts.py`: Registered student attempt lifecycle.
  - `public_quiz.py`: Link-based guest student assessment routes (start, autosave, submit, result).
  - `organizer.py`: Teacher workspace, statistics, teacher-isolated submissions, report export.
  - `admin.py`: Platform supervision, user moderation, audit logs, global stats.
  - `health.py`: System health and readiness probes.
- **Service Layer (`backend/app/services/`)**:
  - `auth_service.py`: Authentication, Argon2id verification, session tokens.
  - `quiz_service.py`: Quiz domain rules, teacher multi-tenancy boundaries, join codes.
  - `public_quiz_service.py`: Authoritative UTC timers, duplicate attempt enforcement, autosave, grading.
  - `admin_service.py`: Platform aggregate telemetry.
  - `audit_service.py`: Scrubbed audit logging.
  - `document_extractor.py`: Zero-dependency universal document parser.
- **Data Model Layer (`backend/app/models/`)**:
  - `user.py`, `quiz.py`, `question.py`, `attempt.py`, `attempt_answer.py`, `audit_log.py`.
- **Client Separation**:
  - Desktop UI cleanly partitioned in `desktop/app/ui/` with API operations encapsulated in `desktop/app/services/api_client.py`.
  - Student Web UI encapsulated in `backend/app/templates/public_quiz.html`.

---

## 2. Configuration Files

### Objective
All environment-specific parameters (ports, secret keys, database URLs, CORS origins, public URLs, token expiry) are isolated from source code and loaded from validated environment configurations.

### Source Code Evidence
- **`backend/app/core/config.py`**:
  - Centralized `Settings` class utilizing Pydantic and `python-dotenv`.
  - Dynamic `SQLALCHEMY_DATABASE_URL` property normalizing Render/Neon `postgres://` URLs to `postgresql+psycopg2://`.
  - Dynamic `PUBLIC_BASE_URL` property auto-detecting host network IP in development or reading cloud domain in production.
  - Safe fallback defaults preventing application crash when running in basic local environments.
- **`backend/.env.example`** & **`QuizFlow/.env.example`**:
  - Clear, sanitized templates documenting all available environment keys without exposing production secrets.
- **`desktop/.env.example`**:
  - Configuration template for the desktop client specifying `QUIZFLOW_API_URL`.

---

## 3. System Settings

### Objective
System-level and runtime administrative options are validated, persistent, and configurable through administrative interfaces without redeploying code.

### Source Code Evidence
- `Settings.ACCESS_TOKEN_EXPIRE_MINUTES`: Configurable session lifetime.
- `Settings.BACKEND_CORS_ORIGINS`: JSON-validated origin whitelist.
- `Settings.ENVIRONMENT` & `Settings.DEBUG`: Fail-closed production toggle.
- Admin Platform Moderation endpoints (`PATCH /api/v1/admin/quizzes/{id}/moderate` and `PATCH /api/v1/admin/users/{id}/status`).
- Desktop Admin Settings Dialog (`SystemSettingsDialog` in `desktop/app/ui/main_window.py`).

---

## 4. Activity Logs

### Objective
Structured, tamper-resistant, audit-compliant event recording with sensitive data scrubbing, unique timestamps, actor identification, and admin searchability.

### Source Code Evidence
- **`backend/app/models/audit_log.py`**:
  - Persistent `audit_logs` table storing `user_id`, `action`, `resource_type`, `resource_id`, `details`, `ip_address`, `created_at`.
- **`backend/app/services/audit_service.py`**:
  - `_sanitize_payload()` recursively scrubs sensitive keys: `password`, `confirm_password`, `token`, `access_token`, `hashed_password`, `secret`.
- **Logged Events**:
  - `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILURE`
  - `USER_REGISTER`, `USER_PROFILE_UPDATE`
  - `QUIZ_CREATE`, `QUIZ_PUBLISH`, `QUIZ_UNPUBLISH`, `QUIZ_DELETE`
  - `PUBLIC_QUIZ_ATTEMPT_START`, `PUBLIC_QUIZ_ATTEMPT_SUBMIT`
- **Admin Querying**:
  - `GET /api/v1/admin/audit-logs` endpoint with filtering by action, user ID, and pagination.

---

## 5. Code Comments & Documentation

### Objective
Meaningful, architectural, and intent-focused documentation that explains *why* complex decisions were made (e.g., server-authoritative timer math, SQLite constraint migration, sanitization algorithms), avoiding trivial or redundant line-by-line restatements.

### Source Code Evidence
- Detailed module docstrings across all services and endpoints.
- Precise inline commentary explaining database schema migrations and concurrency handling in `backend/app/database/init_db.py`.
- Architectural documents:
  - `docs/QUIZFLOW_2_IMPLEMENTATION_PLAN.md`
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY_AUDIT.md`
  - `docs/FEATURE_MATRIX.md`
  - `docs/TQM_MAINTAINABILITY_EVIDENCE.md`
