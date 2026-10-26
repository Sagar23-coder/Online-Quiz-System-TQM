# Online Quiz System

A Python-based desktop application developed as part of the BBAT104 Fundamentals of Total Quality Management project for the academic session 2026–27.

**Quality Goal: Q11 — Improve Maintainability**

## 📌 Project Overview

The Online Quiz System is designed to simplify quiz management, question handling, student assessments, and automatic result calculation.

The application uses Python for its core functionality, Tkinter/CustomTkinter for the graphical user interface, and SQLite for database management.

The primary focus is improving software maintainability through modular programming, centralized configuration, system settings, activity logging, and code comments.

## 🎯 Objectives

- Develop a user-friendly desktop quiz application.
- Provide separate Admin and Student functionality.
- Implement CRUD operations for quizzes and questions.
- Automate quiz evaluation and result calculation.
- Store user, quiz, question, and result data in SQLite.
- Implement all five Q11 maintainability features.
- Improve reliability through input validation and error handling.

## ✨ Key Features

### Admin Module
- Create, view, update, and delete quizzes.
- Manage questions and answer options.
- Configure quiz settings.
- View student results.

### Student Module
- Register and log in.
- View available quizzes.
- Attempt multiple-choice quizzes.
- Submit answers and view results.

### Automatic Grading
- Automatically evaluate submitted answers.
- Calculate quiz scores.
- Store attempts and results.

## 🔧 Q11: Improve Maintainability

| Feature | Description |
|---|---|
| Modular Structure | Organize the application into separate Python modules. |
| Config Files | Centralize application configuration and default values. |
| System Settings | Allow supported application preferences to be configured and saved. |
| Activity Logs | Record important application activities and errors with timestamps. |
| Code Comments | Document important functions and application logic. |

## 🛠️ Technology Stack

- **Language:** Python 3
- **GUI:** Tkinter / CustomTkinter
- **Database:** SQLite
- **IDE:** Visual Studio Code
- **Version Control:** Git and GitHub
- **Testing:** Python `unittest`

## 🏗️ System Architecture

```text
              Online Quiz System
                      |
             +--------+--------+
             |                 |
           Admin             Student
             |                 |
      Quiz Management     Quiz Attempts
             |                 |
             +--------+--------+
                      |
             Application Modules
                      |
          +-----------+-----------+
          |           |           |
       Database   Configuration  Logging
          |
      SQLite DB
```

## 📂 Project Structure

```text
QuizFlow/
│
├─ backend/          ← API server (Python)
│   ├─ app/          ← models, routes, services
│   └─ requirements.txt
│
├─ desktop/          ← Desktop UI (Python‑Tkinter)
│   └─ main.py
│
├─ mobile/           ← Mobile app (React‑Native)
│   ├─ app/          ← screens & navigation
│   └─ package.json
│
├─ docs/             ← Documentation (markdown)
├─ scripts/          ← .bat files to start everything
│
├─ .gitignore        ← Tells Git what **not** to upload
└─ README.md         ← This file (you’re reading it)
```

*The folder structure may be adjusted during development.*

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Sagar23-coder/Online-Quiz-System-TQM.git
```

### 2. Open the Project Directory

```bash
cd Online-Quiz-System-TQM
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python main.py
```

*These commands assume the corresponding source files and dependencies have been implemented.*

## 🧪 Testing

The application will be tested for:

- User registration and authentication.
- Quiz and question CRUD operations.
- Correct automatic grading.
- Database persistence.
- System settings persistence.
- Activity log generation.
- Input validation and error handling.

## 📊 TQM Integration

The project applies Total Quality Management principles through:

- **Customer Focus:** Addressing the needs of administrators and students.
- **Continuous Improvement:** Improving the system through testing and corrective actions.
- **Error Prevention:** Validating inputs and enforcing database constraints.
- **Fact-Based Decisions:** Using test results and defect records to identify problems.
- **Process Improvement:** Documenting application workflows and quality improvements.

### Planned Quality Deliverables

- Software Requirements Specification (SRS)
- System Architecture Flowchart
- SIPOC Process Map
- Critical-to-Quality (CTQ) Tree
- Failure Mode and Effects Analysis (FMEA)
- Defect Log and Checksheet
- Pareto Chart and Fishbone Diagram
- PDCA Improvement Log

## 🔮 Future Enhancements

- Support for additional question types.
- Exportable quiz results and reports.
- Advanced student performance analytics.
- Expanded automated testing.
- Potential web-based version.

## 📚 Project Information

- **Course:** BBAT104 — Fundamentals of Total Quality Management
- **Academic Session:** 2026–27
- **Project:** Online Quiz System
- **Quality Goal:** Q11 — Improve Maintainability

---

*An academic project focused on building a functional and maintainable quiz management application.*
