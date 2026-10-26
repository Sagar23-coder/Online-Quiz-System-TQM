"""
Automated Unit and Integration Tests for AI Quiz Generation, File Import,
and Misconception Detector Analytics.
"""
import pytest
from app.services.ai_generator_service import AIGeneratorService
from app.services.quiz_service import QuizService
from app.models.user import User, UserRole
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.attempt import QuizAttempt, AttemptStatus
from app.models.attempt_answer import AttemptAnswer
from datetime import datetime, timezone, timedelta


def test_ai_generator_local_fallback():
    """Verify local intelligent fallback produces valid quizzes with questions."""
    res = AIGeneratorService.generate_quiz_from_prompt(
        prompt="Python Object Oriented Programming and Encapsulation",
        num_questions=3,
        difficulty="medium",
    )
    assert res is not None
    assert "title" in res
    assert len(res["questions"]) == 3

    for q in res["questions"]:
        assert len(q["question_text"]) > 5
        assert q["option_a"]
        assert q["option_b"]
        assert q["option_c"]
        assert q["option_d"]
        assert q["correct_option"] in ("A", "B", "C", "D")
        assert len(q["explanation"]) > 5


def test_file_import_csv():
    """Verify parsing questions from CSV format."""
    csv_content = """question,option_a,option_b,option_c,option_d,correct_option,explanation,topic
What is Python?,A snake,A programming language,A database,An operating system,B,Python is an interpreted programming language,Python Basics
What is SQL?,Structured Query Language,Simple Query Logic,Standard Queue Line,None,A,SQL is domain-specific language for databases,Databases
"""
    parsed = AIGeneratorService.parse_and_generate_from_file(
        file_content=csv_content,
        filename="test_quiz.csv",
        num_questions=2,
    )
    assert parsed is not None
    assert len(parsed["questions"]) == 2
    assert parsed["questions"][0]["correct_option"] == "B"
    assert parsed["questions"][1]["correct_option"] == "A"
    assert parsed["questions"][0]["topic"] == "Python Basics"


def test_file_import_text_notes():
    """Verify synthesizing questions from document lecture notes."""
    notes = """
Mitochondria generate the majority of cellular energy in eukaryotic organisms through oxidative phosphorylation.
The cell membrane consists of a phospholipid bilayer with embedded transport proteins.
Ribosomes are the cellular machinery responsible for biological protein synthesis.
    """
    parsed = AIGeneratorService.parse_and_generate_from_file(
        file_content=notes,
        filename="Cell_Biology_Notes.txt",
        num_questions=3,
    )
    assert parsed is not None
    assert len(parsed["questions"]) == 3
    for q in parsed["questions"]:
        assert q["correct_option"] == "A"
        assert len(q["explanation"]) > 0


def test_ai_api_endpoints(client, db_session):
    """Test the AI generation endpoint via authenticated organizer."""
    # Create organizer
    org = User(
        email="ai_teacher@test.com",
        full_name="AI Teacher",
        hashed_password="hash",
        role=UserRole.ORGANIZER.value,
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()

    # Login as organizer
    from app.core.security import create_access_token
    token = create_access_token(subject=str(org.id), role=org.role, email=org.email, name=org.full_name)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Generate quiz with AI endpoint
    payload = {
        "prompt": "Relational Databases and SQL Normalization",
        "num_questions": 3,
        "difficulty": "medium",
        "save_directly": True,
    }
    response = client.post("/api/v1/organizer/ai/generate-quiz", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"]
    assert len(data["questions"]) == 3
    assert data["quiz_id"] is not None

    # Check quiz was actually created in DB
    created_quiz = db_session.query(Quiz).filter(Quiz.id == data["quiz_id"]).first()
    assert created_quiz is not None
    assert created_quiz.created_by_id == org.id

    # 2. Import quiz from file endpoint
    csv_payload = {
        "file_content": "question,option_a,option_b,option_c,option_d,correct_option\nIs testing important?,No,Yes,Never,Maybe,B\n",
        "filename": "qa_quiz.csv",
        "num_questions": 1,
        "difficulty": "easy",
        "save_directly": True,
    }
    res_file = client.post("/api/v1/organizer/ai/import-file-quiz", json=csv_payload, headers=headers)
    assert res_file.status_code == 200
    file_data = res_file.json()
    assert file_data["quiz_id"] is not None


def test_misconception_detector_analytics(db_session):
    """Verify distractor clustering and topic breakdown in QuizService.get_quiz_report."""
    # Create organizer & student
    org = User(email="prof_calc@test.com", full_name="Prof Calculus", hashed_password="h", role=UserRole.ORGANIZER.value, is_active=True)
    st1 = User(email="student1@test.com", full_name="Student One", hashed_password="h", role=UserRole.STUDENT.value, is_active=True)
    st2 = User(email="student2@test.com", full_name="Student Two", hashed_password="h", role=UserRole.STUDENT.value, is_active=True)
    db_session.add_all([org, st1, st2])
    db_session.commit()

    # Create quiz with 1 question tagged with topic
    quiz = Quiz(
        title="Calculus Quiz",
        subject="Mathematics",
        duration_minutes=20,
        passing_percentage=50,
        total_marks=2,
        is_published=True,
        created_by_id=org.id,
    )
    db_session.add(quiz)
    db_session.commit()

    q1 = Question(
        quiz_id=quiz.id,
        question_text="What is the derivative of e^x?",
        option_a="e^x",
        option_b="x * e^(x-1)",
        option_c="ln(x)",
        option_d="1/x",
        correct_option="A",
        marks=1,
        topic="Exponential Functions",
        difficulty="medium",
        order_index=1,
    )
    db_session.add(q1)
    db_session.commit()

    # Student 1 attempts and picks distractor B
    att1 = QuizAttempt(
        student_id=st1.id,
        quiz_id=quiz.id,
        status=AttemptStatus.COMPLETED.value,
        deadline_time=datetime.now(timezone.utc) + timedelta(minutes=10),
        score_obtained=0.0,
        total_marks=1.0,
        percentage=0.0,
        is_passed=False,
    )
    # Student 2 attempts and also picks distractor B (Clustering!)
    att2 = QuizAttempt(
        student_id=st2.id,
        quiz_id=quiz.id,
        status=AttemptStatus.COMPLETED.value,
        deadline_time=datetime.now(timezone.utc) + timedelta(minutes=10),
        score_obtained=0.0,
        total_marks=1.0,
        percentage=0.0,
        is_passed=False,
    )
    db_session.add_all([att1, att2])
    db_session.commit()

    ans1 = AttemptAnswer(attempt_id=att1.id, question_id=q1.id, selected_option="B", is_correct=False, marks_awarded=0.0)
    ans2 = AttemptAnswer(attempt_id=att2.id, question_id=q1.id, selected_option="B", is_correct=False, marks_awarded=0.0)
    db_session.add_all([ans1, ans2])
    db_session.commit()

    # Call get_quiz_report
    report = QuizService.get_quiz_report(db_session, quiz.id, user_id=org.id, is_admin=False)
    assert report is not None
    assert report.total_attempts == 2
    assert report.average_score == 0.0

    # Verify distractor analysis identified option B clustering
    q_stat = report.question_stats[0]
    assert q_stat.common_wrong_option == "B"
    assert q_stat.common_wrong_count == 2
    assert q_stat.common_wrong_percentage == 100.0

    # Verify misconception detector detected the pattern
    assert len(report.misconceptions) >= 1
    m = report.misconceptions[0]
    assert m["common_distractor"] == "B"
    assert m["topic"] == "Exponential Functions"

    # Verify Topic Breakdown
    assert len(report.topic_breakdown) >= 1
    assert report.topic_breakdown[0]["topic"] == "Exponential Functions"
    assert report.topic_breakdown[0]["accuracy_percentage"] == 0.0

    # Verify Teacher Action Center recommendations generated
    assert len(report.recommended_actions) >= 1
    action_titles = [a["title"] for a in report.recommended_actions]
    assert any("Schedule Revision" in t for t in action_titles)
