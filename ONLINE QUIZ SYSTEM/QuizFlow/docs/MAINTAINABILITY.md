# QuizFlow — Software Maintainability Specification (Q11)

This document formalizes the architectural design decisions and concrete implementations delivered in **QuizFlow** to address the five core pillars of software maintainability: Modularity, Configuration Management, Code Reusability, Logging & Error Handling, and Documentation & Code Quality.

---

## 1. Modularity

### Definition & Objective
High cohesion and loose coupling across presentation, business logic, API routing, and persistent storage. Prevents monolithic code files, enabling isolated refactoring, independent testing, and team scalability.

### Concrete Implementation Locations
- **API Routing**: `backend/app/api/v1/`
  - `auth.py`: Student registration, JWT login, and profile access.
  - `quizzes.py`: Admin quiz management and student quiz discovery.
  - `questions.py`: MCQ question management.
  - `attempts.py`: Attempt lifecycle, answer autosave, and submission.
  - `admin.py`: Aggregated platform statistics and student audit logs.
  - `health.py`: System diagnostics and database ping.
- **Service Layer**: `backend/app/services/`
  - `auth_service.py`: Authentication, credential validation, token generation.
  - `quiz_service.py`: Business validation rules for publishing and question tracking.
  - `attempt_service.py`: Server-side scoring, deadline calculation, and duplicate submission prevention.
  - `admin_service.py`: Real database aggregation metrics.
- **Database & Models**: `backend/app/models/` and `backend/app/database/`
  - `user.py`, `quiz.py`, `question.py`, `attempt.py`, `attempt_answer.py`.
- **Desktop Separation**: `desktop/app/ui/` and `desktop/app/services/api_client.py`.
- **Mobile Separation**: `mobile/app/screens/`, `mobile/services/`, `mobile/navigation/`.

### Why It Improves Maintainability
Changes to quiz publishing logic (such as requiring a minimum pass threshold) only touch `quiz_service.py` without impacting the desktop or mobile UI code.

### Verification Procedure
1. Run `pytest -v tests/test_quizzes.py` to test quiz service logic independently.
2. Run `ruff check app` to verify zero circular imports or architectural violations.

---

## 2. Configuration Management

### Definition & Objective
Centralizing environment-specific parameters (database connection strings, JWT cryptographic secrets, network host/ports, token expiry) outside of application source code.

### Concrete Implementation Locations
- `backend/app/core/config.py`: Unified `Settings` class loading from environment variables and `.env` files with sane fallback defaults.
- `backend/.env.example`: Secure template documenting all environment keys without disclosing production credentials.
- `mobile/services/config.ts`: `NetworkConfig` class detecting runtime platforms (`10.0.2.2:8000` for Android emulator, `localhost:8000` for Web/iOS, or custom LAN IP for physical mobile devices).
- `desktop/app/services/api_client.py`: Configurable `base_url` reading `QUIZFLOW_API_URL`.

### Why It Improves Maintainability
Eliminates hardcoded credentials and localhost IPs. Allows zero-code re-targeting between local SQLite development, Dockerized testing, and cloud PostgreSQL staging.

### Verification Procedure
1. Create a `.env` in `backend/` with a modified `DATABASE_URL` or `PROJECT_NAME`.
2. Start the backend with `scripts/start_backend.bat` and observe that `http://localhost:8000/health` immediately reflects the updated configuration.

---

## 3. Code Reusability

### Definition & Objective
Adhering to the DRY (Don't Repeat Yourself) principle through reusable UI components, centralized API communication clients, and standard validation routines.

### Concrete Implementation Locations
- **Centralized API Clients**:
  - `desktop/app/services/api_client.py`: Singleton `ApiClient` handling authentication headers, request execution, and network error handling.
  - `mobile/services/api.ts`: Centralized `ApiService` handling fetch requests and session tokens.
- **UI Design System Components**:
  - `desktop/app/components/stat_card.py`: Reusable SaaS metric card with status accent indicators.
  - `desktop/app/utils/theme.py`: Color tokens, fonts, and styling constants.
- **Pydantic Validation Schemas**:
  - `backend/app/schemas/`: Reusable validation logic across create, update, and response serialization.

### Why It Improves Maintainability
Any update to network retry behavior or error translation is made once in `api_client.py` and immediately applies to all 10+ desktop views.

### Verification Procedure
1. Review `desktop/app/ui/admin_dashboard_view.py`: All 5 metric cards instantiate `StatCard` with zero duplicate Tkinter widget setup code.

---

## 4. Logging and Error Handling

### Definition & Objective
Systematic diagnostics, structured request logging, and secure exception handling that prevents leaking sensitive server internals to clients.

### Concrete Implementation Locations
- **Request Logging Middleware**: `backend/app/main.py`
  - Captures method, path, HTTP status, and response latency in milliseconds (`log_requests`).
- **Validation Exception Handler**: `backend/app/main.py`
  - Catches `RequestValidationError` and transforms Pydantic exceptions into clean, JSON-serializable responses (`detail`, `errors`).
- **Non-Leaking Error Messages**: `backend/app/services/auth_service.py`
  - Generic `"Incorrect email or password"` protects against user enumeration.
  - Passwords and JWT tokens are NEVER logged to console or logs.
- **Resilient UI Error Handling**:
  - `desktop/app/services/api_client.py`: Gracefully intercepts `ConnectionError` and `Timeout`, returning user-friendly messages rather than crashing the Tkinter event loop.

### Why It Improves Maintainability
Developers can inspect live server logs to diagnose issues within seconds, while end users receive clear, actionable feedback rather than unhandled tracebacks.

### Verification Procedure
1. Launch `scripts/start_backend.bat`.
2. Send an invalid payload or login request; inspect the console output to observe formatted timestamped logs without credential exposure.

---

## 5. Documentation and Code Quality

### Definition & Objective
Readable code with explicit type annotations, docstrings, automated formatting, automated test suites, and beginner-friendly setup guides.

### Concrete Implementation Locations
- **Type Hints**: Full typing across backend models, schemas, services, and mobile TypeScript definitions (`mobile/types/index.ts`).
- **Automated Test Suite**: `backend/tests/`
  - 22 automated test cases verifying health, authentication, permissions, publishing logic, and server-side scoring.
- **Static Analysis & Linting**: `backend/pyproject.toml`
  - Ruff configured for strict PEP 8 and modern Python conventions.
- **Interactive OpenAPI Documentation**: Generated automatically at `http://localhost:8000/docs` and `http://localhost:8000/redoc`.
- **System Documentation**:
  - `README.md`: Beginner-friendly setup and operational manual.
  - `PROJECT_REPORT.md`: Academic software engineering and TQM report.
  - `docs/MAINTAINABILITY.md`: Maintainability design specification.
  - `docs/BUILD_STATUS.md`: Live implementation and test tracking log.

### Why It Improves Maintainability
New developers can onboard within minutes, type checkers prevent subtle runtime bugs, and the automated test suite guards against regressions.

### Verification Procedure
1. Run `ruff check app tests` (reports `All checks passed!`).
2. Run `pytest -v` (reports `22 passed in 8.41s`).
3. Run `npx tsc --noEmit` in `mobile/` (reports 0 type errors).

