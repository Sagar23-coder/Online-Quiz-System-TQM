"""
Phase 4 Verification Test: AI Question Quality Checker & Bilingual Localization
Tests:
1. Pedagogical Quality Evaluation on Well-Formed Question (High Score)
2. Flawed Question Detection (Duplicate choices, giveaway clue, negative ambiguity)
3. Hindi/English Bilingual Translation Engine
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.ai_quality_service import AIQualityService

def test_phase4():
    print("=" * 60)
    print("PHASE 4: AI QUESTION QUALITY CHECKER & LOCALIZATION TESTS")
    print("=" * 60)

    # 1. Test Well-Crafted Question
    print("\n[1] Testing Well-Formed Assessment Question...")
    good_q = {
        "question_text": "In relational database design, what is the primary purpose of Third Normal Form (3NF)?",
        "option_a": "Eliminate transitive functional dependencies",
        "option_b": "Ensure all table columns are strictly atomic",
        "option_c": "Enforce cross-table foreign key constraints",
        "option_d": "Maximize index storage and query throughput",
        "correct_option": "A",
        "explanation": "3NF removes transitive dependencies where non-prime attributes depend on other non-prime attributes."
    }

    good_res = AIQualityService.audit_question_quality(**good_q)
    print(f"  ✓ High Quality Question Score: {good_res['quality_score']}/100 (Rating: {good_res['rating']})")
    assert good_res["quality_score"] >= 85, f"Expected high quality score >= 85, got {good_res['quality_score']}"
    assert len(good_res["warnings"]) == 0, f"Expected 0 warnings for good question, got {good_res['warnings']}"

    # 2. Test Flawed Question
    print("\n[2] Testing Detection of Pedagogical Flaws (Duplicates, Length Clue, Negative Stems)...")
    flawed_q = {
        "question_text": "Which of the following is not a quality tool?",  # uncapitalized negative word
        "option_a": "Pareto Chart",
        "option_b": "Pareto Chart",  # DUPLICATE OPTION!
        "option_c": "Fishbone Diagram",
        "option_d": "This is an extremely long option that describes an entirely different concept and gives away the whole answer because it is much longer than the others",
        "correct_option": "D",
        "explanation": ""
    }

    flawed_res = AIQualityService.audit_question_quality(**flawed_q)
    print(f"  ✓ Flawed Question Score: {flawed_res['quality_score']}/100 (Rating: {flawed_res['rating']})")
    print(f"  ✓ Warnings Captured ({flawed_res['warnings_count']}):")
    for w in flawed_res["warnings"]:
        print(f"    - [{w['severity']}] {w['message']}")

    assert flawed_res["quality_score"] <= 60, f"Expected low score for flawed question, got {flawed_res['quality_score']}"
    assert flawed_res["warnings_count"] >= 3, "Expected at least 3 warnings!"

    # 3. Test Bilingual Localization Engine
    print("\n[3] Testing English to Hindi Bilingual Localization Engine...")
    trans = AIQualityService.translate_question_bilingual(
        question_text=good_q["question_text"],
        option_a=good_q["option_a"],
        option_b=good_q["option_b"],
        option_c=good_q["option_c"],
        option_d=good_q["option_d"],
        explanation=good_q["explanation"]
    )

    print(f"  ✓ Translated Prompt (HI): {trans['question_text_hi'][:60]}...")
    print(f"  ✓ Translated Option A (HI): {trans['option_a_hi']}")
    assert "डेटाबेस" in trans["question_text_hi"] or "प्राथमिक" in trans["question_text_hi"]
    print("  ✓ Hindi vocabulary mapping verified cleanly.")

    print("\n" + "=" * 60)
    print("PHASE 4 TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase4()
