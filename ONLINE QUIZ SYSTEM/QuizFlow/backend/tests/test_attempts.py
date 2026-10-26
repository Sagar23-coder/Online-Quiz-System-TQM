"""
Tests for quiz attempts, timer enforcement, server-side grading, and duplicate prevention.
"""


def _create_published_quiz(client, admin_token):
    create_res = client.post(
        "/api/v1/quizzes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Networking Basics",
            "description": "OSI model quiz",
            "duration_minutes": 10,
            "passing_percentage": 50,
        },
    )
    quiz_id = create_res.json()["id"]

    # Question 1: correct is A
    client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "question_text": "What protocol is used for secure web browsing?",
            "option_a": "HTTPS",
            "option_b": "FTP",
            "option_c": "Telnet",
            "option_d": "SNMP",
            "correct_option": "A",
            "marks": 5,
            "explanation": "HTTPS provides encrypted communication over TLS.",
        },
    )

    # Question 2: correct is C
    client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "question_text": "Which layer of the OSI model does IP operate at?",
            "option_a": "Physical",
            "option_b": "Data Link",
            "option_c": "Network",
            "option_d": "Transport",
            "correct_option": "C",
            "marks": 5,
            "explanation": "IP (Internet Protocol) operates at Layer 3, Network Layer.",
        },
    )

    client.post(
        f"/api/v1/quizzes/{quiz_id}/publish",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return quiz_id


def test_student_quiz_attempt_flow(client, admin_token, student_token):
    quiz_id = _create_published_quiz(client, admin_token)

    # 1. Start quiz attempt
    start_res = client.post(
        f"/api/v1/attempts/quizzes/{quiz_id}/start",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert start_res.status_code == 201
    start_data = start_res.json()
    attempt_id = start_data["attempt_id"]
    questions = start_data["questions"]
    assert len(questions) == 2

    # Verify SECURITY requirement: correct_option and explanation must NOT be sent to student!
    for q in questions:
        assert "correct_option" not in q
        assert "explanation" not in q

    q1_id = questions[0]["id"]
    q2_id = questions[1]["id"]

    # 2. Save answer for Question 1 (Correct: A)
    ans1_res = client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"question_id": q1_id, "selected_option": "A"},
    )
    assert ans1_res.status_code == 200
    assert ans1_res.json()["saved"] is True

    # 3. Save answer for Question 2 (Incorrect: B instead of C)
    ans2_res = client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"question_id": q2_id, "selected_option": "B"},
    )
    assert ans2_res.status_code == 200

    # 4. Finish/Submit attempt
    finish_res = client.post(
        f"/api/v1/attempts/{attempt_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert finish_res.status_code == 200
    result_data = finish_res.json()

    assert result_data["attempt_id"] == attempt_id
    assert result_data["status"] == "completed"
    assert result_data["score_obtained"] == 5.0  # Q1 was correct (5 marks), Q2 was incorrect (0 marks)
    assert result_data["total_marks"] == 10.0
    assert result_data["percentage"] == 50.0
    assert result_data["is_passed"] is True
    assert result_data["correct_count"] == 1
    assert result_data["incorrect_count"] == 1
    assert result_data["unattempted_count"] == 0

    # 5. Prevent duplicate submission!
    dup_res = client.post(
        f"/api/v1/attempts/{attempt_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert dup_res.status_code == 400
    assert "already been completed" in dup_res.json()["detail"].lower()


def test_cannot_save_answer_after_completion(client, admin_token, student_token):
    quiz_id = _create_published_quiz(client, admin_token)
    start_res = client.post(
        f"/api/v1/attempts/quizzes/{quiz_id}/start",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    attempt_id = start_res.json()["attempt_id"]
    q1_id = start_res.json()["questions"][0]["id"]

    # Submit immediately
    client.post(
        f"/api/v1/attempts/{attempt_id}/finish",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # Attempting to save answer now must fail
    res = client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"question_id": q1_id, "selected_option": "A"},
    )
    assert res.status_code == 400

