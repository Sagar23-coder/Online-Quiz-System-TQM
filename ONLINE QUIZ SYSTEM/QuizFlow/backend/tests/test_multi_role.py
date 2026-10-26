"""
Comprehensive Multi-Role Platform Tests: Admin, Organizer, and Participant.
Verifies role-based access control, quiz ownership isolation, join codes, attempt limits,
result release controls, CSV reports, user account suspension, and audit logs.
"""


def test_multi_role_registration_and_validation(client):
    # 1. Register as Participant
    p_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "student_alice@example.com",
            "full_name": "Alice Participant",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "participant",
        },
    )
    assert p_res.status_code == 201
    assert p_res.json()["role"] == "participant"

    # 2. Register as Organizer
    o_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher_bob@example.com",
            "full_name": "Bob Organizer",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "organizer",
        },
    )
    assert o_res.status_code == 201
    assert o_res.json()["role"] == "organizer"

    # 3. Reject public registration attempt as Admin
    a_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "hacker@example.com",
            "full_name": "Wannabe Admin",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "admin",
        },
    )
    assert a_res.status_code == 422
    assert "public registration" in a_res.text.lower()


def test_organizer_quiz_ownership_isolation(client):
    # Register two organizers
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "org1@example.com",
            "full_name": "Organizer One",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "organizer",
        },
    )
    t1_res = client.post(
        "/api/v1/auth/login",
        json={"email": "org1@example.com", "password": "Password123!"},
    )
    token1 = t1_res.json()["access_token"]

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "org2@example.com",
            "full_name": "Organizer Two",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "organizer",
        },
    )
    t2_res = client.post(
        "/api/v1/auth/login",
        json={"email": "org2@example.com", "password": "Password123!"},
    )
    token2 = t2_res.json()["access_token"]

    # Organizer 1 creates a quiz
    q_res = client.post(
        "/api/v1/quizzes",
        json={
            "title": "Organizer 1 Chemistry Test",
            "description": "Organic chemistry basics",
            "duration_minutes": 20,
            "passing_percentage": 60,
            "is_public": False,
            "max_attempts": 2,
            "release_results_immediately": False,
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert q_res.status_code == 201
    q_data = q_res.json()
    quiz_id = q_data["id"]
    join_code = q_data["join_code"]
    assert join_code.startswith("QF-")

    # Organizer 1 adds question
    q_add = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        json={
            "question_text": "What is the atomic number of Carbon?",
            "option_a": "6",
            "option_b": "12",
            "option_c": "14",
            "option_d": "8",
            "correct_option": "A",
            "marks": 5,
            "explanation": "Carbon has 6 protons.",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert q_add.status_code == 201
    question_id = q_add.json()["id"]

    # Organizer 2 attempts to edit Organizer 1's quiz -> MUST BE 403 Forbidden!
    edit_res = client.put(
        f"/api/v1/quizzes/{quiz_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert edit_res.status_code == 403

    # Organizer 2 attempts to update Organizer 1's question -> MUST BE 403 Forbidden!
    q_edit = client.put(
        f"/api/v1/questions/{question_id}",
        json={"marks": 10},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert q_edit.status_code == 403

    # Organizer 2 attempts to delete Organizer 1's quiz -> MUST BE 403 Forbidden!
    del_res = client.delete(
        f"/api/v1/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert del_res.status_code == 403

    # Organizer 1 publishes the quiz
    pub_res = client.post(
        f"/api/v1/quizzes/{quiz_id}/publish",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["is_published"] is True


def test_participant_join_code_and_result_release_flow(client):
    # 1. Organizer creates a private quiz with results held until released
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "prof_smith@example.com",
            "full_name": "Prof Smith",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "organizer",
        },
    )
    t_org = client.post(
        "/api/v1/auth/login",
        json={"email": "prof_smith@example.com", "password": "Password123!"},
    ).json()["access_token"]

    q_res = client.post(
        "/api/v1/quizzes",
        json={
            "title": "Advanced Quantum Mechanics",
            "description": "Private midterm test",
            "duration_minutes": 15,
            "passing_percentage": 50,
            "is_public": False,
            "max_attempts": 1,
            "release_results_immediately": False,
        },
        headers={"Authorization": f"Bearer {t_org}"},
    )
    quiz_id = q_res.json()["id"]
    join_code = q_res.json()["join_code"]

    client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        json={
            "question_text": "What is Planck's constant unit?",
            "option_a": "Joule-second",
            "option_b": "Newton-meter",
            "option_c": "Watt-hour",
            "option_d": "Kilogram",
            "correct_option": "A",
            "marks": 10,
            "explanation": "Action is expressed in Joule-seconds.",
        },
        headers={"Authorization": f"Bearer {t_org}"},
    )
    client.post(f"/api/v1/quizzes/{quiz_id}/publish", headers={"Authorization": f"Bearer {t_org}"})

    # 2. Participant registers and joins via code
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "part_charlie@example.com",
            "full_name": "Charlie Student",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "participant",
        },
    )
    t_student = client.post(
        "/api/v1/auth/login",
        json={"email": "part_charlie@example.com", "password": "Password123!"},
    ).json()["access_token"]

    # Test joining with invalid code
    bad_code = client.post(
        "/api/v1/quizzes/join-by-code",
        json={"join_code": "INVALID99"},
        headers={"Authorization": f"Bearer {t_student}"},
    )
    assert bad_code.status_code == 404

    # Join with valid code
    join_res = client.post(
        "/api/v1/quizzes/join-by-code",
        json={"join_code": join_code},
        headers={"Authorization": f"Bearer {t_student}"},
    )
    assert join_res.status_code == 200
    assert join_res.json()["id"] == quiz_id

    # 3. Attempt the quiz
    start_res = client.post(
        f"/api/v1/attempts/quizzes/{quiz_id}/start",
        headers={"Authorization": f"Bearer {t_student}"},
    )
    assert start_res.status_code == 201
    attempt_id = start_res.json()["attempt_id"]
    question_id = start_res.json()["questions"][0]["id"]

    # Submit answer
    client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_id": question_id, "selected_option": "A"},
        headers={"Authorization": f"Bearer {t_student}"},
    )

    # Finish quiz
    finish_res = client.post(
        f"/api/v1/attempts/{attempt_id}/finish",
        headers={"Authorization": f"Bearer {t_student}"},
    )
    assert finish_res.status_code == 200
    res_data = finish_res.json()
    assert res_data["results_released"] is False
    # Correct option and explanation MUST NOT be leaked to student yet!
    assert res_data["review"][0]["correct_option"] is None
    assert "not yet been released" in res_data["review"][0]["explanation"]

    # 4. Verify max attempt limit enforcement: trying to start second attempt must fail!
    second_start = client.post(
        f"/api/v1/attempts/quizzes/{quiz_id}/start",
        headers={"Authorization": f"Bearer {t_student}"},
    )
    assert second_start.status_code == 400
    assert "maximum" in second_start.text.lower()

    # 5. Organizer checks report and exports CSV
    report_res = client.get(
        f"/api/v1/organizer/quizzes/{quiz_id}/report",
        headers={"Authorization": f"Bearer {t_org}"},
    )
    assert report_res.status_code == 200
    assert report_res.json()["total_attempts"] == 1
    assert report_res.json()["attempts"][0]["student_email"] == "part_charlie@example.com"

    csv_res = client.get(
        f"/api/v1/organizer/quizzes/{quiz_id}/export-csv",
        headers={"Authorization": f"Bearer {t_org}"},
    )
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "part_charlie@example.com" in csv_res.text

    # 6. Organizer releases results
    rel_res = client.post(
        f"/api/v1/organizer/quizzes/{quiz_id}/release-results",
        headers={"Authorization": f"Bearer {t_org}"},
    )
    assert rel_res.status_code == 200
    assert rel_res.json()["results_released"] is True

    # 7. Student checks results again -> now answers are fully visible!
    student_res = client.get(
        f"/api/v1/attempts/{attempt_id}/result",
        headers={"Authorization": f"Bearer {t_student}"},
    )
    assert student_res.status_code == 200
    assert student_res.json()["results_released"] is True
    assert student_res.json()["review"][0]["correct_option"] == "A"
    assert student_res.json()["score_obtained"] == 10.0


def test_admin_moderation_suspension_and_audit(client, admin_token):
    # 1. Register a participant
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "troublemaker@example.com",
            "full_name": "Trouble Maker",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "participant",
        },
    )
    user = client.post(
        "/api/v1/auth/login",
        json={"email": "troublemaker@example.com", "password": "Password123!"},
    ).json()["user"]
    user_id = user["id"]

    # 2. Admin searches users
    users_res = client.get(
        "/api/v1/admin/users?search=troublemaker",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert users_res.status_code == 200
    assert len(users_res.json()) >= 1

    # 3. Admin suspends the user
    suspend_res = client.post(
        f"/api/v1/admin/users/{user_id}/status",
        json={"is_active": False, "reason": "Academic integrity violation"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert suspend_res.status_code == 200
    assert suspend_res.json()["is_active"] is False

    # 4. Suspended user attempts login -> MUST BE 403 Forbidden!
    blocked_login = client.post(
        "/api/v1/auth/login",
        json={"email": "troublemaker@example.com", "password": "Password123!"},
    )
    assert blocked_login.status_code == 403
    assert "suspended" in blocked_login.text.lower()

    # 5. Admin reactivates the user
    reactivate_res = client.post(
        f"/api/v1/admin/users/{user_id}/status",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["is_active"] is True

    # 6. Admin checks audit logs
    audit_res = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0
    actions = [log_item["action"] for log_item in logs]
    assert "USER_SUSPEND" in actions
    assert "USER_REACTIVATE" in actions

    # 7. Admin platform reports
    reports_res = client.get(
        "/api/v1/admin/platform-reports",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reports_res.status_code == 200
    assert "role_distribution" in reports_res.json()
