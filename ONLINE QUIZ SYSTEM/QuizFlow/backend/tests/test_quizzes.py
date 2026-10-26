"""
Tests for quiz creation, question management, publishing rules, and student visibility.
"""


def test_admin_create_quiz(client, admin_token):
    response = client.post(
        "/api/v1/quizzes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Data Structures Basics",
            "description": "Foundational test on stacks and queues",
            "duration_minutes": 20,
            "passing_percentage": 50,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Data Structures Basics"
    assert data["is_published"] is False
    assert data["total_marks"] == 0


def test_student_cannot_create_quiz(client, student_token):
    response = client.post(
        "/api/v1/quizzes",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"title": "Unauthorized Quiz", "duration_minutes": 10, "passing_percentage": 50},
    )
    assert response.status_code == 403


def test_publish_empty_quiz_fails(client, admin_token):
    # Create empty quiz
    create_res = client.post(
        "/api/v1/quizzes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Empty Quiz", "duration_minutes": 15, "passing_percentage": 50},
    )
    quiz_id = create_res.json()["id"]

    # Try to publish without questions
    publish_res = client.post(
        f"/api/v1/quizzes/{quiz_id}/publish",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert publish_res.status_code == 400
    assert "no questions" in publish_res.json()["detail"].lower()


def test_add_question_and_publish_quiz(client, admin_token):
    # Create quiz
    create_res = client.post(
        "/api/v1/quizzes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Algorithms 101", "duration_minutes": 15, "passing_percentage": 50},
    )
    quiz_id = create_res.json()["id"]

    # Add question
    q_res = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "question_text": "What is the worst-case time complexity of binary search?",
            "option_a": "O(1)",
            "option_b": "O(log n)",
            "option_c": "O(n)",
            "option_d": "O(n^2)",
            "correct_option": "B",
            "marks": 2,
            "explanation": "Binary search divides the search space in half each iteration.",
        },
    )
    assert q_res.status_code == 201
    assert q_res.json()["marks"] == 2

    # Now publish should succeed
    pub_res = client.post(
        f"/api/v1/quizzes/{quiz_id}/publish",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["is_published"] is True
    assert pub_res.json()["total_marks"] == 2


def test_student_quiz_visibility(client, admin_token, student_token):
    # Create draft quiz
    draft_res = client.post(
        "/api/v1/quizzes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Secret Draft Quiz", "duration_minutes": 10, "passing_percentage": 50},
    )
    draft_id = draft_res.json()["id"]

    # Student requests list of published quizzes
    list_res = client.get("/api/v1/quizzes")
    assert list_res.status_code == 200
    quiz_ids = [q["id"] for q in list_res.json()]
    assert draft_id not in quiz_ids

