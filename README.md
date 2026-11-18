# QuizFlow 2.0 — Intelligent Assessment & Learning Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![CustomTkinter](https://img.shields.io/badge/Desktop-CustomTkinter-2b5b84.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-4169E1.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Audit%20Passed-success.svg)](docs/SECURITY_AUDIT.md)

QuizFlow 2.0 is a modern, secure, and accessible educational assessment platform designed for teachers, academic institutions, and students. Built with an enterprise-grade architecture, QuizFlow combines a high-performance **FastAPI cloud backend**, an intuitive **CustomTkinter desktop management studio** for educators, a responsive **HTML5 web assessment portal** for students, and a **React Native mobile client**.

---

## Architecture Overview

```
                          ┌──────────────────────────────────────────────┐
                          │         QuizFlow Cloud Backend (FastAPI)     │
                          │   - RESTful API & SSE / WebSocket Services   │
                          │   - Public Student Web Assessment Engine    │
                          │   - SQLAlchemy 2.0 ORM & Alembic Migrations  │
                          │   - Multi-Tenant Row-Level Security         │
                          └──────────────────────┬───────────────────────┘
                                                 │
                        ┌────────────────────────┼────────────────────────┐
                        ▼                        ▼                        ▼
      ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
      │  CustomTkinter Desktop   │  │   Public Web Portal      │  │   React Native Mobile    │
      │   Teacher / Admin App    │  │ (Any Browser, Mobile/PC) │  │      Student Client      │
      │  - Quiz Authoring        │  │ - 3-Screen Assessment    │  │  - Cross-platform Native │
      │  - Question Bank Manager │  │ - Anti-Cheating Controls │  │  - Push Notifications    │
      │  - Advanced Analytics    │  │ - Deterministic Shuffling│  │  - Offline Mode Support  │
      │  - Profile Management    │  │ - Instant Scorecard      │  │                          │
      └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘
                                                 │
                                                 ▼
                          ┌──────────────────────────────────────────────┐
                          │       Persistent Relational Database         │
                          │   - Production: Neon Cloud PostgreSQL       │
                          │   - Local Development: SQLite               │
                          └──────────────────────────────────────────────┘
```

---

## Key Features

### 🎓 Dual Assessment Modes
- **Secure Exam Mode:** Enforces academic integrity with fullscreen tracking, tab-switch anomaly detection, copy/paste locking, right-click restrictions, and immutable audit logs of suspicious events.
- **Practice Mode:** Provides instant answer verification, detailed pedagogical explanations, and self-paced learning without penalty triggers.

### 📚 Reusable Question Bank & Tagging
- Centralized question repository organized by subject, grade level, topic, and Bloom's taxonomy difficulty.
- Tag-based filtering and batch import into newly scheduled or existing quizzes.
- Automated duplicate question detection to maintain repository hygiene.

### 🤖 AI Question Quality Checker & Hindi Localization
- Automated heuristic analysis of question stems for readability, clarity, and ambiguity.
- Quality scoring of answer distractors with automatic flagging of low-quality or identical options.
- Bilingual evaluation engine supporting seamless English and Hindi (हिन्दी) localization.

### 📊 Deep Learning Analytics & Remediation
- Comprehensive difficulty ratings and question discrimination index (Point-Biserial correlation).
- Distractor selection frequency distribution charts to uncover student misconceptions.
- Automated, actionable remediation prompts tailored to low-performing cohorts.

### 🔒 Enterprise-Grade Security & Isolation
- **Strict Multi-Tenant Teacher Isolation:** Row-level data isolation guarantees that teachers can only view, edit, and access their own quizzes, questions, banks, and student submissions.
- **Academic Integrity Safeguards:** Deterministic per-student question and option shuffling prevents answer copying across adjacent devices.
- **Hardened Authentication:** Argon2 and bcrypt password hashing with progressive, IP-aware brute-force rate limiting.
- **Full Audit Trail:** High-resolution audit logging capturing all security events, quiz exports, and credential updates.

### 📱 Streamlined Student Assessment Flow
- **Screen 1 — Candidate Intake:** Minimal, accessible details form with validation for name, class, and section/roll number.
- **Screen 2 — Focused Assessment:** Single-question card interface with clear pagination, timer countdown, and responsive controls across mobile and desktop displays.
- **Screen 3 — Instant Scorecard:** Real-time celebration screen showing final percentage, category breakdown, and detailed question-by-question review.

---

## Tech Stack

| Component | Technology | Description |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Asynchronous, high-throughput REST API backend |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | Production ASGI server with multi-worker scaling |
| **ORM / Data Layer** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Type-safe SQL toolkit and Object Relational Mapper |
| **Desktop GUI** | [CustomTkinter](https://customtkinter.tomschimansky.com/) | Modern, themed desktop interface for Windows/macOS/Linux |
| **Database** | [PostgreSQL](https://www.postgresql.org/) / SQLite | Neon Cloud PostgreSQL (Production) / SQLite (Dev) |
| **Web Frontend** | HTML5, CSS3, Vanilla JavaScript | Zero-framework, lightweight, accessible student portal |
| **Mobile App** | [React Native](https://reactnative.dev/) / Expo | Cross-platform student mobile application |
| **Security & Auth** | Argon2 / bcrypt / PyJWT | Cryptographic hashing and stateless JWT tokens |
| **Deployment** | [Render](https://render.com/) | Fully managed cloud web services with SSL automation |

---

## Project Structure

```
QuizFlow/
├── backend/                  # FastAPI Application & Web Assessment Engine
│   ├── app/
│   │   ├── api/v1/endpoints/ # REST API endpoints (auth, quizzes, questions, etc.)
│   │   ├── core/             # Security, JWT, rate limiting, and app configuration
│   │   ├── db/               # Database session, models, and base schema
│   │   ├── models/           # SQLAlchemy entity models
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Business logic, AI audits, analytics, and grading
│   │   └── templates/        # Responsive Jinja2 student assessment templates
│   ├── .env.example          # Environment variables template for backend
│   ├── main.py               # Backend entry point and ASGI application factory
│   └── requirements.txt      # Python dependencies for backend service
├── desktop/                  # CustomTkinter Teacher & Admin Desktop Studio
│   ├── app/
│   │   ├── controllers/      # Client controllers interfacing with backend APIs
│   │   ├── models/           # Desktop domain data models
│   │   ├── services/         # Desktop network client and persistence services
│   │   └── ui/               # Responsive CustomTkinter views and dialogs
│   ├── main.py               # Desktop application launcher
│   └── requirements.txt      # Desktop application dependencies
├── mobile/                   # React Native Student Assessment Client
│   ├── assets/               # Application icons and splash screens
│   ├── src/                  # Navigation, screens, and components
│   └── package.json          # Node.js dependencies for mobile client
├── docs/                     # Architectural, security, and maintenance documentation
│   ├── ARCHITECTURE.md       # Full architectural specification
│   ├── FEATURE_MATRIX.md     # Phase-by-phase feature implementation record
│   └── SECURITY_AUDIT.md     # Application security audit and vulnerability log
├── scripts/                  # Management, migration, and verification scripts
│   ├── migrate_sqlite_to_pg.py # Automated SQLite to PostgreSQL migration tool
│   ├── security_audit_scanner.py # Pre-commit secret and vulnerability scanner
│   └── verify_quizflow_2_full.py # Full platform automated test suite
├── .env.example              # Root environment template
├── .gitignore                # Production git exclusion rules
├── render.yaml               # Render Infrastructure-as-Code deployment manifest
└── START_QUIZFLOW.bat        # Windows one-click local developer launcher
```

---

## Getting Started

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** 18.x or higher (for Mobile client)
- **Git:** 2.30 or higher

---

### 1. Setting Up the Backend

1. Navigate to the backend directory:
   ```bash
   cd QuizFlow/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment template and configure:
   ```bash
   cp .env.example .env
   ```
5. Start the backend development server:
   ```bash
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```
   The interactive API documentation will be available at:
   - **Swagger UI:** `http://127.0.0.1:8000/docs`
   - **ReDoc:** `http://127.0.0.1:8000/redoc`
   - **Health Probe:** `http://127.0.0.1:8000/health`

---

### 2. Setting Up the Desktop Application

1. Open a new terminal and navigate to the desktop directory:
   ```bash
   cd QuizFlow/desktop
   ```
2. Activate your virtual environment and install desktop requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the desktop application:
   ```bash
   python main.py
   ```
   *Tip: By default, the desktop client connects to `http://127.0.0.1:8000/api/v1`. To connect to a cloud backend, set the environment variable `QUIZFLOW_API_URL=https://your-backend.onrender.com/api/v1`.*

---

### 3. Setting Up the Mobile Client

1. Navigate to the mobile directory:
   ```bash
   cd QuizFlow/mobile
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Expo development server:
   ```bash
   npx expo start
   ```

---

## Environment Configuration

QuizFlow uses environment variables for all environment-specific settings. Never commit active `.env` files to source control.

| Variable | Description | Example / Recommended Setting |
|---|---|---|
| `ENVIRONMENT` | Deployment environment mode | `development` or `production` |
| `DEBUG` | FastAPI debug mode flag | `False` in production |
| `PROJECT_NAME` | Project title string | `QuizFlow` |
| `SECRET_KEY` | Cryptographic secret for signing tokens | High-entropy 32-byte hex string |
| `DATABASE_URL` | SQLAlchemy connection URI | `postgresql+psycopg2://...` or `sqlite:///quizflow.db` |
| `PUBLIC_BASE_URL` | Public web address for student quiz links | `https://quizflow-backend.onrender.com` |
| `BACKEND_CORS_ORIGINS` | Permitted CORS origins (JSON array) | `["https://quizflow-backend.onrender.com","*"]` |
| `QUIZFLOW_API_URL` | Target API URL for Desktop clients | `https://quizflow-backend.onrender.com/api/v1` |

---

## Cloud Deployment (Render + Neon PostgreSQL)

QuizFlow is fully prepared for cloud deployment using [Render](https://render.com/) and [Neon](https://neon.tech/).

### Step 1: Provision Neon Cloud Database
1. Create a free account at [Neon.tech](https://neon.tech).
2. Create a new PostgreSQL database named `quizflow`.
3. Copy your connection string (format: `postgresql+psycopg2://user:password@host/quizflow?sslmode=require`).

### Step 2: Deploy Backend to Render
1. Connect your GitHub repository to Render.
2. Render will automatically detect the provided [render.yaml](render.yaml) blueprint:
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Set the required environment variables in Render's dashboard:
   - `DATABASE_URL`: Your Neon connection string.
   - `SECRET_KEY`: A cryptographically secure random string.
   - `PUBLIC_BASE_URL`: Your Render service URL (e.g., `https://quizflow-backend.onrender.com`).

### Step 3: Run Data Migration (Optional)
To safely migrate your historical local SQLite records to Neon PostgreSQL without data loss:
```bash
python scripts/migrate_sqlite_to_pg.py --sqlite-path backend/quizflow.db --pg-url "your_neon_url"
```

---

## Automated Testing & Quality Assurance

QuizFlow includes a comprehensive verification suite validating all 13 development phases:

```bash
# Run the complete platform verification suite
python scripts/verify_quizflow_2_full.py

# Run backend unit and integration tests
cd backend && pytest -v
```

The automated test suite verifies:
- Multi-tenant teacher data isolation across all endpoints.
- Secure Exam Mode anti-cheating audit trail.
- Question bank CRUD and tag-based search.
- AI question quality evaluation algorithms.
- Analytics calculations and remediation suggestions.
- Zero-downtime database health probes (< 5ms latency).

---

## Security & Academic Integrity

- **Strict Access Control:** Endpoints require JWT bearer token authentication with role-based permissions (`admin`, `teacher`, `student`).
- **Data Protection:** Passwords are never stored in plaintext. Passwords adhere to strict complexity requirements (8+ characters, uppercase, lowercase, numbers, symbols).
- **Rate Limiting:** Brute-force protection limits failed login attempts progressively.
- **Reporting Vulnerabilities:** If you discover a security vulnerability in QuizFlow, please disclose it responsibly via a private issue or contact the maintainers directly.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
