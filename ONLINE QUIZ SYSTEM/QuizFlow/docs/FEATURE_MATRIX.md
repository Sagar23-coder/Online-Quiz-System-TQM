# QUIZFLOW 2.0 — COMPREHENSIVE FEATURE MATRIX

| Feature Category | Specific Capability | Target Audience | Backend Endpoint | Persistence Model | UI Implementation | Status |
| :--- | :--- | :---: | :--- | :--- | :--- | :---: |
| **Authentication & Profile** | Teacher/Admin Login (PBKDF2/Argon2) | Teacher / Admin | `POST /api/v1/auth/login` | `users` table | Desktop & Web | ✅ Active & Verified |
| | Teacher Registration & Policy | Teacher | `POST /api/v1/auth/register` | `users` table | Desktop & Web | ✅ Active & Verified |
| | Teacher Profile & Password Update | Teacher | `PUT /api/v1/auth/profile` | `users` table | Desktop Modal | ✅ Active & Verified |
| | Brute-force Login Rate Limiter | All | Middleware / Service | In-memory sliding window | HTTP 429 Lockout | ✅ Active & Verified |
| **Public Assessment** | Link-based Student Taking | Public Student | `GET /quiz/{share_token}` | None (public link) | Responsive HTML/JS | ✅ Active & Verified |
| | Guest Student Identity Capture | Public Student | `POST /api/v1/public-quiz/{token}/start` | `quiz_attempts` | Web form | ✅ Active & Verified |
| | Server-Authoritative UTC Timer | Public Student | Calculated server-side | `quiz_attempts.deadline_time` | Sticky countdown | ✅ Active & Verified |
| | Real-time Answer Autosave | Public Student | `POST /api/v1/public-quiz/attempt/{token}/save-answer` | `attempt_answers` | Web option cards | ✅ Active & Verified |
| | Instant Result Grading & Review | Public Student | `POST /api/v1/public-quiz/attempt/{token}/submit` | `quiz_attempts` | Web scorecard | ✅ Active & Verified |
| **Secure Exam vs. Practice Mode** | Server-side Auto-Finalization | Student / Teacher | `PublicQuizService._check_deadline` | `quiz_attempts.status` | Auto-lock screen | ✅ Active & Verified |
| | Practice Mode Instant Feedback & Hints | Public Student | `POST /api/v1/public-quiz/attempt/{token}/check-answer` | Stateless inspection | "💡 Check Answer" card | ✅ Active & Verified |
| | Question & Option Randomization | Public Student | Per-attempt seed generation | `quiz_attempts.question_order_seed` | Scrambled cards | ✅ Active & Verified |
| | Tab Visibility & Integrity Event Logging | Student / Teacher | `POST /api/v1/public-quiz/attempt/{token}/integrity-event` | `quiz_attempts.integrity_events` | `visibilitychange` listener | ✅ Active & Verified |
| **Question Bank** | Centralized Reusable Question Bank | Teacher | `GET/POST /api/v1/question-banks` | `question_banks` | Desktop Bank View | ✅ Active & Verified |
| | Bloom's Taxonomy & Reusable Items | Teacher | `GET/POST /api/v1/question-banks/{id}/items` | `question_bank_items` | Bank Item Inspector | ✅ Active & Verified |
| | 1-Click Import into Active Quizzes | Teacher | `POST /api/v1/question-banks/{id}/import-to-quiz/{quiz_id}` | `questions` | Desktop Import Action | ✅ Active & Verified |
| | Multi-Question Types (MCQ, MSQ, T/F, Short) | Teacher / Student | Question Type discriminator | `questions.question_type` | Dynamic form fields | ✅ Active & Verified |
| | Universal File Importer (.pdf, .docx)| Teacher | `POST /api/v1/organizer/ai/import-file-quiz` | Parsed questions | Desktop Dialog | ✅ Active & Verified |
| **AI Question Quality** | Structural Syntax Validator | Teacher | `POST /api/v1/ai/validate-question` | None (stateless) | Quality Inspector | ✅ Active & Verified |
| | Distractor Plausibility & Ambiguity | Teacher | `POST /api/v1/ai/validate-question` | Quality score & warnings | Quality Inspector | ✅ Active & Verified |
| | English/Hindi Question Translation | Teacher | `POST /api/v1/ai/translate-question` | `questions.*_hi` | Quality Inspector | ✅ Active & Verified |
| **Analytics & Reports** | Teacher Dashboard & Stats | Teacher | `GET /api/v1/organizer/dashboard-stats` | Aggregated queries | Desktop Dashboard | ✅ Active & Verified |
| | Teacher-Isolated Submissions List | Teacher | `GET /api/v1/organizer/results` | `quiz_attempts` | Desktop Submissions | ✅ Active & Verified |
| | Distractor Frequency & Mastery Tiers | Teacher | `GET /api/v1/organizer/quizzes/{id}/report` | Aggregated attempts | Desktop Report Modal | ✅ Active & Verified |
| | Gradebook CSV Export | Teacher | `GET /api/v1/organizer/quizzes/{id}/export-csv` | Streaming CSV | Save Dialog | ✅ Active & Verified |
| **Live Quiz Mode** | Ephemeral PIN Lobby (`LIVE-XXXX`) | Teacher / Student | `POST /api/v1/live/create` | `live_sessions` | Web/Desktop Lobby | ✅ Active & Verified |
| | Synchronized Question State | Teacher / Student | `GET /api/v1/live/{pin}/state` | In-memory + DB | Live Console | ✅ Active & Verified |
| | Speed-Weighted Gamified Scoring | Student | `POST /api/v1/live/{pin}/answer` | `live_participants` | Speed score card | ✅ Active & Verified |
| | Real-time Leaderboard Podium | Teacher / Student | `POST /api/v1/live/{pin}/end` | Ranked participants | Desktop Host Podium | ✅ Active & Verified |
| **Accessibility (WCAG 2.2)** | High-Contrast Theme Toggle | Student | `toggleContrast()` in web portal | CSS variable overrides | "🌓 Contrast" button | ✅ Active & Verified |
| | Keyboard-Only Operation (1-4, Enter)| Student / Teacher | JavaScript keydown listeners | ARIA roles | Full keyboard flow | ✅ Active & Verified |
| **Audit & Reliability** | Tamper-Resistant Structured Logging | Admin / System | `AuditService.log` | `audit_logs` | Admin Audit View | ✅ Active & Verified |
| | Database Health & Readiness Latency Probes | System / DevOps | `GET /health` & `GET /health/ready` | `SELECT 1` ping | Health endpoint | ✅ Active & Verified |
