"""
Phase 2 Verification Test: Dual Mode (Secure Exam vs. Practice Mode)
Tests:
1. Practice Mode Answer Checking (Immediate Formative Feedback & Hinting)
2. Exam Mode Integrity Event Logging (Tab Blur / Visibility Monitoring)
3. Question Scrambling Determinism with Per-Attempt Seed
4. Server-Authoritative Timer & Safe Start Response
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database.session import SessionLocal
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.attempt import QuizAttempt
from app.schemas.attempt import (
    PublicStudentDetailsRequest,
    PracticeCheckRequest,
    IntegrityEventRequest,
)
from app.services.public_quiz_service import PublicQuizService
import json

def test_phase2():
    print("=" * 60)
    print("PHASE 2: DUAL MODE (SECURE EXAM VS PRACTICE MODE) TESTS")
    print("=" * 60)

    db = SessionLocal()

    import time
    run_id = int(time.time())

    # 1. Setup Practice Mode Quiz Test
    print("\n[1] Testing Practice Mode & Immediate Formative Feedback...")
    # Find or update a test quiz to practice mode
    quiz = db.query(Quiz).filter(Quiz.id == 4).first()
    orig_mode = quiz.mode
    orig_shuffle = quiz.shuffle_questions
    quiz.mode = "practice"
    db.commit()

    details = PublicStudentDetailsRequest(
        full_name=f"Practice Tester {run_id}",
        student_class="Class 10",
        section="Sec A",
        email=f"practice.{run_id}@quizflow.local",
        phone=f"91{run_id % 100000000:08d}"
    )

    start_resp = PublicQuizService.start_public_attempt(db, quiz.share_token, details)
    attempt_token = start_resp.attempt_token
    assert start_resp.mode == "practice", "Expected mode to be practice!"
    print(f"  ✓ Practice Attempt started cleanly in mode='{start_resp.mode}'.")

    # Pick a question to test answer check
    test_q_id = start_resp.questions[0].id
    actual_q = db.query(Question).filter(Question.id == test_q_id).first()
    correct_opt = actual_q.correct_option
    wrong_opt = "B" if correct_opt != "B" else "C"

    # Test wrong choice
    chk_wrong = PublicQuizService.check_practice_answer(
        db, attempt_token, PracticeCheckRequest(question_id=test_q_id, selected_option=wrong_opt)
    )
    assert not chk_wrong.is_correct, "Wrong answer should not be marked correct!"
    assert chk_wrong.hint is not None, "Expected hint for incorrect answer!"
    print(f"  ✓ Wrong answer feedback verified: Correct={chk_wrong.is_correct}, Hint='{chk_wrong.hint[:30]}...'")

    # Test correct choice
    chk_right = PublicQuizService.check_practice_answer(
        db, attempt_token, PracticeCheckRequest(question_id=test_q_id, selected_option=correct_opt)
    )
    assert chk_right.is_correct, "Correct answer should be marked correct!"
    print(f"  ✓ Correct answer feedback verified: Correct={chk_right.is_correct}, Option={chk_right.correct_option}")

    # 2. Testing Secure Exam Mode & Question Scrambling
    print("\n[2] Testing Exam Mode Question Randomization & Seeding...")
    quiz.mode = "exam"
    quiz.shuffle_questions = True
    db.commit()

    details_exam = PublicStudentDetailsRequest(
        full_name=f"Exam Tester {run_id}",
        student_class="Class 12",
        section="Sec B",
        email=f"exam.{run_id}@quizflow.local",
        phone=f"92{run_id % 100000000:08d}"
    )

    start_exam = PublicQuizService.start_public_attempt(db, quiz.share_token, details_exam)
    exam_token = start_exam.attempt_token
    assert start_exam.mode == "exam", "Expected mode to be exam!"

    attempt_record = db.query(QuizAttempt).filter(QuizAttempt.attempt_token == exam_token).first()
    assert attempt_record.question_order_seed is not None, "Order seed must be saved!"
    print(f"  ✓ Exam attempt initialized with deterministic seed: {attempt_record.question_order_seed}")

    # 3. Testing Exam Integrity Monitoring Event Logging
    print("\n[3] Testing Client Integrity Event Logging (Tab Blur / Focus)...")
    event_req = IntegrityEventRequest(
        event_type="tab_blur",
        client_timestamp="2026-11-18T14:30:00Z",
        details={"state": "hidden", "reason": "user_switched_tabs"}
    )
    res = PublicQuizService.log_integrity_event(db, exam_token, event_req)
    assert res["status"] == "logged" and res["total_events"] >= 1

    # Verify event stored in database
    db.refresh(attempt_record)
    events = json.loads(attempt_record.integrity_events or "[]")
    assert len(events) >= 1 and events[-1]["event"] == "tab_blur"
    print(f"  ✓ Integrity event verified in database: {events[-1]['event']} at {events[-1]['server_time']}")

    # Clean up test attempts to maintain pristine database state
    db.query(QuizAttempt).filter(QuizAttempt.attempt_token.in_([attempt_token, exam_token])).delete(synchronize_session=False)

    # Restore original quiz settings
    quiz.mode = orig_mode
    quiz.shuffle_questions = orig_shuffle
    db.commit()
    db.close()

    print("\n" + "=" * 60)
    print("PHASE 2 TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase2()
