"""
Phase 3 Verification Test: Teacher Question Bank & Rich Question Types
Tests:
1. Question Bank Creation with Subject & Topic Categorization
2. Adding Questions to Bank (with Bloom's taxonomy & rich types)
3. 1-Click Import from Question Bank into Teacher's Quiz
4. Strict Multi-Tenancy: Another Teacher Blocked from Bank Access
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database.session import SessionLocal
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.question_bank import QuestionBank, QuestionBankItem
from app.schemas.question_bank import QuestionBankCreate, QuestionBankItemCreate
from app.services.question_bank_service import QuestionBankService
from fastapi import HTTPException

def test_phase3():
    print("=" * 60)
    print("PHASE 3: TEACHER QUESTION BANK & REPOSITORY TESTS")
    print("=" * 60)

    db = SessionLocal()
    teacher_id = 8  # Sharma Sir

    # 1. Create Question Bank
    print("\n[1] Creating Question Bank Repository...")
    bank_in = QuestionBankCreate(
        title="TQM Quality Assurance Core Questions",
        subject="Total Quality Management",
        topic="Kaizen & Six Sigma",
        difficulty="medium",
        grade_level="B.Tech 5th Sem",
        description="Comprehensive repository of TQM statistical methods and quality tools."
    )
    bank_resp = QuestionBankService.create_bank(db, teacher_id=teacher_id, bank_in=bank_in)
    bank_id = bank_resp.id
    assert bank_resp.id > 0 and bank_resp.title == bank_in.title
    print(f"  ✓ Question Bank created: ID={bank_id}, Title='{bank_resp.title}'")

    # 2. Add Questions to Bank
    print("\n[2] Adding Diverse Questions to Bank...")
    q1_in = QuestionBankItemCreate(
        question_text="Which of the following describes the primary objective of Kaizen in TQM?",
        question_type="single_choice",
        option_a="Continuous incremental improvement",
        option_b="Complete system replacement",
        option_c="Periodic external audit",
        option_d="Defect concealment",
        correct_option="A",
        marks=2,
        cognitive_level="understand",
        difficulty="medium",
        explanation="Kaizen refers to continuous, ongoing incremental improvement involving all employees."
    )
    item1 = QuestionBankService.add_item_to_bank(db, bank_id=bank_id, teacher_id=teacher_id, item_in=q1_in)

    q2_in = QuestionBankItemCreate(
        question_text="In Six Sigma methodology, what defect rate per million opportunities is targeted?",
        question_type="single_choice",
        option_a="3.4 defects per million",
        option_b="34 defects per million",
        option_c="340 defects per million",
        option_d="0.34 defects per million",
        correct_option="A",
        marks=2,
        cognitive_level="remember",
        difficulty="hard",
        explanation="Six Sigma strives for 3.4 defects per million opportunities (DPMO)."
    )
    item2 = QuestionBankService.add_item_to_bank(db, bank_id=bank_id, teacher_id=teacher_id, item_in=q2_in)

    details = QuestionBankService.get_bank_details(db, bank_id=bank_id, teacher_id=teacher_id)
    assert details.item_count == 2
    print(f"  ✓ Added 2 questions to Bank. Total items verified: {details.item_count}")

    # 3. Import Selected Questions into Quiz 4 (Owned by Teacher 8)
    print("\n[3] Testing 1-Click Import into Teacher's Quiz...")
    quiz = db.query(Quiz).filter(Quiz.id == 4).first()
    orig_q_count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
    orig_marks = quiz.total_marks

    imported_cnt = QuestionBankService.import_items_to_quiz(
        db, bank_id=bank_id, quiz_id=quiz.id, teacher_id=teacher_id, item_ids=[item1.id, item2.id]
    )
    assert imported_cnt == 2, f"Expected 2 imported questions, got {imported_cnt}"

    db.refresh(quiz)
    new_q_count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
    print(f"  ✓ Import Success: {imported_cnt} questions transferred into Quiz 4.")
    print(f"    - Question count increased: {orig_q_count} -> {new_q_count}")
    print(f"    - Total marks updated: {orig_marks} -> {quiz.total_marks}")

    # Clean up imported questions so we don't pollute live demo quiz permanently
    imported_qs = db.query(Question).filter(
        Question.quiz_id == quiz.id,
        Question.question_text.in_([q1_in.question_text, q2_in.question_text])
    ).all()
    for iq in imported_qs:
        db.delete(iq)
    quiz.total_marks = orig_marks
    db.commit()
    print(f"  ✓ Temporary imported quiz questions cleaned up; Quiz 4 restored.")

    # 4. Strict Multi-Tenancy: Teacher 4 (Shivam) attempting to access Teacher 8's Bank
    print("\n[4] Testing Multi-Tenancy Data Isolation on Question Bank...")
    try:
        QuestionBankService.get_bank_details(db, bank_id=bank_id, teacher_id=4)
        print("  ✕ FAIL: Teacher 4 was allowed to access Teacher 8's question bank!")
        assert False
    except HTTPException as e:
        assert e.status_code == 403
        print(f"  ✓ PASS: Teacher 4 blocked with HTTP {e.status_code} ({e.detail})")

    # Clean up test bank
    QuestionBankService.delete_bank(db, bank_id=bank_id, teacher_id=teacher_id)
    print(f"  ✓ Test Question Bank cleanly removed.")

    db.close()
    print("\n" + "=" * 60)
    print("PHASE 3 TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase3()
