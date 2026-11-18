# QUIZFLOW 2.0 — SYSTEM ARCHITECTURE SPECIFICATION

```
                           ┌──────────────────────────────────────────────┐
                           │               STUDENT CLIENTS                │
                           │   (Public Mobile Web / Desktop Browser / App)│
                           └──────────────────────┬───────────────────────┘
                                                  │
                                                  │ HTTPS / WebSockets
                                                  ▼
┌────────────────────────┐         ┌──────────────────────────────────────┐
│ TEACHER / ADMIN DESKTOP│         │        FASTAPI APPLICATION LAYER     │
│   (CustomTkinter App)  ├────────►│   - Security & Rate-Limiting Middlewares│
│ - Quiz Builder         │ REST API│   - Role-Based Access Control (RBAC) │
│ - Question Bank        │ Bearer  │   - Exam Engine & Authoritative Timer│
│ - Live Session Console │ JWT     │   - AI Quality Review & Distractor Engine
│ - Analytics & Grading  │         │   - WebSocket Live Session Hub       │
└────────────────────────┘         └──────────────┬───────────────────────┘
                                                  │
                                                  │ SQLAlchemy 2.0 ORM
                                                  ▼
                                   ┌──────────────────────────────────────┐
                                   │      PERSISTENT DATABASE LAYER       │
                                   │  - Local Dev: SQLite (WAL Mode)      │
                                   │  - Cloud Prod: Neon / Managed Postgres│
                                   │  - Additive, Dialect-Agnostic Schema │
                                   └──────────────────────────────────────┘
```

---

## 1. Core Component Breakdown

### A. Presentation & Client Layers
1. **Public Student Web Assessment Portal (`backend/app/templates/public_quiz.html`)**:
   - Single-Page Responsive Web Application (vanilla HTML5, modern CSS3, ES6+ JS).
   - Zero compilation requirement; served directly by FastAPI.
   - Dual-mode capability: Secure Timed Exam Mode vs. Practice Mode.
   - Low-bandwidth tolerant with resilient client-side retry queue.
   - WCAG 2.2 AA compliant with keyboard navigation, live ARIA regions, and high contrast.
2. **Teacher & Administrator Desktop Client (`desktop/`)**:
   - Built on CustomTkinter (`ctk`) with a modern dark navy/indigo SaaS aesthetic.
   - Responsive multi-resolution window manager (`860x540` to `4K`).
   - Integrated Question Bank, Live Quiz Controller, AI Quality Workspace, and Analytics Dashboard.
3. **Mobile Client (`mobile/`)**:
   - React Native & Expo mobile application consuming QuizFlow 2.0 REST endpoints.

---

### B. Backend Services Layer (`backend/app/services/`)
- **`auth_service.py`**: User authentication, Argon2id hashing, JWT generation, password updates, rate limiting.
- **`quiz_service.py`**: Quiz lifecycle, publishing workflows, shareable link tokenization, teacher data isolation.
- **`public_quiz_service.py`**: Server-authoritative timer, guest participant registration, answer autosave, atomic submission, auto-finalization on deadline expiration.
- **`question_bank_service.py`**: Question cataloging, cognitive taxonomy (Bloom's), tagging, versioning, question reuse across quizzes.
- **`ai_quality_service.py`**: Deterministic structural validation + semantic language review, distractor plausibility check, reading grade level, English/Hindi translation.
- **`analytics_service.py`**: Item difficulty ($P$), discrimination index ($D$), misconception analysis, score distribution, class-level comparisons.
- **`live_session_service.py`**: Live session state machine, short-lived 6-digit PIN management, lobby coordinator, live scoreboard.
- **`audit_service.py`**: Tamper-resistant audit trail with PII redaction and structured event logging.
- **`document_extractor.py`**: Pure-Python zero-dependency universal document extractor (PDF, PPTX, DOCX, XLSX, CSV, TXT, images).

---

### C. Database Architecture & Data Entities

```
 ┌───────────────┐        1:N       ┌────────────────┐
 │     users     ├─────────────────►│    quizzes     │
 │ (Admin/Teacher│                  └───────┬────────┘
 └───────┬───────┘                          │
         │                                  │ 1:N
         │ 1:N                              ▼
         │                          ┌────────────────┐        N:1       ┌────────────────┐
         │                          │   questions    ├─────────────────►│ question_banks │
         │                          └───────┬────────┘                  └────────────────┘
         │                                  │
         │                                  │ 1:N
         ▼                                  ▼
 ┌───────────────┐        1:N       ┌────────────────┐
 │ quiz_attempts ├─────────────────►│ attempt_answers│
 └───────────────┘                  └────────────────┘
```

1. **`users`**: Platform administrators and teachers/organizers (`id`, `email`, `full_name`, `hashed_password`, `role`, `is_active`, `created_at`, `updated_at`).
2. **`quizzes`**: Quizzes created by teachers (`id`, `title`, `subject`, `description`, `instructions`, `duration_minutes`, `passing_percentage`, `total_marks`, `is_published`, `join_code`, `share_token`, `mode`, `is_share_link_active`, `max_attempts`, `release_results_policy`, `created_by_id`, `created_at`).
3. **`questions`**: Individual quiz questions (`id`, `quiz_id`, `question_bank_id`, `question_text`, `question_type`, `option_a`, `option_b`, `option_c`, `option_d`, `options_json`, `correct_option`, `correct_answer_json`, `marks`, `explanation`, `order_index`, `topic`, `difficulty`, `cognitive_level`, `source`).
4. **`question_banks`**: Reusable question repository organized by teacher and taxonomy (`id`, `teacher_id`, `title`, `subject`, `grade_level`, `chapter`, `tags`, `is_shared_institution`).
5. **`quiz_attempts`**: Student assessment attempts (`id`, `quiz_id`, `student_id`, `participant_name`, `participant_class`, `participant_section`, `participant_email`, `participant_phone`, `attempt_token`, `start_time`, `deadline_time`, `end_time`, `status`, `score_obtained`, `total_marks`, `percentage`, `is_passed`, `mode`, `question_order_seed`, `accommodations_extra_minutes`).
6. **`attempt_answers`**: Autosaved and final student responses (`id`, `attempt_id`, `question_id`, `selected_option`, `answer_text`, `is_correct`, `marks_awarded`, `answered_at`).
7. **`live_sessions`**: Teacher-hosted real-time quiz sessions (`id`, `quiz_id`, `teacher_id`, `session_pin`, `status`, `current_question_index`, `is_instructor_paced`, `created_at`).
8. **`audit_logs`**: Immutable security and event trail (`id`, `user_id`, `action`, `resource_type`, `resource_id`, `details`, `ip_address`, `created_at`).

---

## 2. Multi-Tenant Teacher Data Boundary
- Every query affecting a teacher's quizzes, reports, analytics, questions, or live sessions explicitly includes:
  `WHERE created_by_id = :current_teacher_id` or `WHERE teacher_id = :current_teacher_id`.
- Admins possess platform-wide supervisory read access, but individual teachers are strictly sandboxed within their own tenant domain.
- Public students access assessments solely through unguessable 64-character tokens (`share_token`) or ephemeral session PINs, preventing unauthorized quiz enumeration.
