"""
Phase 5 & 6 Verification Test: Advanced Analytics & Synchronized Live Quiz Mode
Tests:
1. Psychometric Analytics & Teacher Remediation Actions
2. Live Assessment Lifecycle (Lobby -> Active -> Fast Answer Points -> Next -> Podium)
3. Multi-Tenancy Security on Live Sessions (Teacher A cannot control Teacher B's live quiz)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database.session import SessionLocal
from app.services.quiz_service import QuizService
from app.services.live_quiz_service import LiveQuizService
from fastapi import HTTPException

def test_phase5_and_6():
    print("=" * 60)
    print("PHASE 5 & 6: ANALYTICS & LIVE QUIZ MODE VERIFICATION")
    print("=" * 60)

    db = SessionLocal()
    teacher_id = 8  # Sharma Sir (Owner of Quiz 4)

    # 1. Test Advanced Psychometric Analytics & Misconceptions (Phase 5)
    print("\n[1] Testing Advanced Analytics & Learning Intelligence (Phase 5)...")
    report = QuizService.get_quiz_report(db, quiz_id=4, user_id=teacher_id)
    assert report.quiz_id == 4, "Report quiz id mismatch"
    print(f"  ✓ Exam Report loaded for '{report.title}'")
    print(f"    - Total Attempts: {report.total_attempts}")
    print(f"    - Unique Participants: {report.unique_participants}")
    print(f"    - Average Score: {report.average_score}%")
    print(f"    - Pass Rate: {report.pass_percentage}%")
    print(f"    - Misconception Clusters Detected: {len(report.misconceptions)}")
    print(f"    - Topic Mastery Categories: {len(report.topic_breakdown)}")
    print(f"    - Teacher Action Center Items: {len(report.recommended_actions)}")
    for act in report.recommended_actions[:2]:
        print(f"      * [{act['priority']}] {act['title']}")

    # 2. Test Synchronized Live Quiz Lifecycle (Phase 6)
    print("\n[2] Testing Live Classroom Quiz Mode Lifecycle (Phase 6)...")
    live_info = LiveQuizService.create_session(db, teacher_id=teacher_id, quiz_id=4)
    pin = live_info["session_pin"]
    print(f"  ✓ Live Session created! PIN: {pin}, Status: {live_info['status']}")

    # Two students join
    p1 = LiveQuizService.join_session(db, pin=pin, nickname="Alice Explorer")
    p2 = LiveQuizService.join_session(db, pin=pin, nickname="Bob Challenger")
    print(f"  ✓ 2 Students joined lobby: '{p1['nickname']}' and '{p2['nickname']}'")

    state_lobby = LiveQuizService.get_session_state(db, pin=pin)
    assert state_lobby["total_participants"] == 2
    assert state_lobby["status"] == "lobby"

    # Teacher starts session
    started = LiveQuizService.start_session(db, pin=pin, teacher_id=teacher_id)
    assert started["status"] == "active"
    print(f"  ✓ Live session started by teacher. Question #1 live!")

    state_active = LiveQuizService.get_session_state(db, pin=pin, participant_token=p1["participant_token"])
    cq = state_active["current_question"]
    assert cq is not None and "question_text" in cq
    q1_id = cq["question_id"]

    # Student 1 (Alice) answers quickly (1.5 seconds) with 'A'
    ans1 = LiveQuizService.submit_answer(
        db, pin=pin, participant_token=p1["participant_token"], question_id=q1_id, selected_option="A", time_spent_sec=1.5
    )
    print(f"  ✓ Alice answered: Correct={ans1['is_correct']}, Points Earned={ans1['points_earned']} (Streak: {ans1['streak']})")

    # Student 2 (Bob) answers slowly with wrong option
    wrong_opt = "B" if ans1["correct_option"] != "B" else "C"
    ans2 = LiveQuizService.submit_answer(
        db, pin=pin, participant_token=p2["participant_token"], question_id=q1_id, selected_option=wrong_opt, time_spent_sec=10.0
    )
    print(f"  ✓ Bob answered: Correct={ans2['is_correct']}, Points Earned={ans2['points_earned']}")

    # Check leaderboard
    state_after_q1 = LiveQuizService.get_session_state(db, pin=pin)
    lb = state_after_q1["leaderboard"]
    print(f"  ✓ Real-time Leaderboard Top 2: #1 {lb[0]['nickname']} ({lb[0]['score']} pts), #2 {lb[1]['nickname']} ({lb[1]['score']} pts)")
    assert lb[0]["nickname"] == "Alice Explorer" and lb[0]["score"] > lb[1]["score"]

    # Teacher advances question
    nxt = LiveQuizService.next_question(db, pin=pin, teacher_id=teacher_id)
    print(f"  ✓ Teacher advanced question: Status={nxt['status']}, Current Q={nxt.get('current_question_index')}")

    # Teacher ends session & shows podium
    podium_res = LiveQuizService.end_session(db, pin=pin, teacher_id=teacher_id)
    assert podium_res["status"] == "ended"
    assert len(podium_res["podium"]) >= 1
    winner = podium_res["podium"][0]
    print(f"  ✓ Session ended! Winner on Podium: {winner['nickname']} ({winner['score']} pts, Rank #{winner['rank']})")

    # 3. Test Multi-Tenancy on Live Sessions
    print("\n[3] Testing Multi-Tenancy Authorization on Live Sessions...")
    try:
        LiveQuizService.start_session(db, pin=pin, teacher_id=4)  # Teacher 4 trying to operate Teacher 8's session
        print("  ✕ FAIL: Teacher 4 was allowed to control Teacher 8's live session!")
        assert False
    except HTTPException as e:
        assert e.status_code == 403
        print(f"  ✓ PASS: Teacher 4 blocked from Teacher 8's live session (HTTP {e.status_code}: {e.detail})")

    db.close()
    print("\n" + "=" * 60)
    print("PHASE 5 & 6 TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase5_and_6()
