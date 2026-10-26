"""
Centralized API Client for QuizFlow Desktop Application.
Manages JWT authentication tokens, endpoint calls, and structured error handling.
"""
import os
from typing import Any, Dict, Optional, Tuple
import requests

DEFAULT_BASE_URL = os.getenv("QUIZFLOW_API_URL", "http://127.0.0.1:8000/api/v1")


class ApiClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.user_data: Optional[Dict[str, Any]] = None
        self.session = requests.Session()

    def set_base_url(self, url: str) -> None:
        self.base_url = url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(
        self, method: str, path: str, json_data: Any = None, timeout: int = 10
    ) -> Tuple[bool, Any]:
        url = f"{self.base_url}{path}"
        try:
            res = self.session.request(
                method=method,
                url=url,
                headers=self._headers(),
                json=json_data,
                timeout=timeout,
            )
            if res.status_code in (200, 201):
                return True, res.json()
            try:
                err_data = res.json()
                msg = err_data.get("detail", res.text)
                return False, msg
            except Exception:
                return False, f"Server Error ({res.status_code}): {res.text}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to QuizFlow server. Ensure backend is running at " + self.base_url
        except requests.exceptions.Timeout:
            return False, "Network request timed out. Please check your connection."
        except Exception as e:
            return False, f"Unexpected network error: {str(e)}"

    # System Health
    def check_health(self) -> Tuple[bool, Any]:
        return self._request("GET", "/health", timeout=5)

    # Authentication
    def login(self, email: str, password: str) -> Tuple[bool, Any]:
        ok, data = self._request("POST", "/auth/login", {"email": email, "password": password})
        if ok and "access_token" in data:
            self.token = data["access_token"]
            self.user_data = data.get("user")
        return ok, data

    def register(
        self,
        email: str,
        full_name: str,
        password: str,
        confirm_password: str,
        role: str = "participant",
    ) -> Tuple[bool, Any]:
        return self._request(
            "POST",
            "/auth/register",
            {
                "email": email,
                "full_name": full_name,
                "password": password,
                "confirm_password": confirm_password,
                "role": role,
            },
        )

    def logout(self) -> None:
        self.token = None
        self.user_data = None

    def get_me(self) -> Tuple[bool, Any]:
        return self._request("GET", "/auth/me")

    # Admin Operations
    def get_dashboard_stats(self) -> Tuple[bool, Any]:
        return self._request("GET", "/admin/dashboard-stats")

    def get_admin_quizzes(self) -> Tuple[bool, Any]:
        return self._request("GET", "/quizzes/admin/all")

    def create_quiz(self, quiz_data: Dict[str, Any]) -> Tuple[bool, Any]:
        return self._request("POST", "/quizzes", quiz_data)

    def update_quiz(self, quiz_id: int, quiz_data: Dict[str, Any]) -> Tuple[bool, Any]:
        return self._request("PUT", f"/quizzes/{quiz_id}", quiz_data)

    def delete_quiz(self, quiz_id: int) -> Tuple[bool, Any]:
        return self._request("DELETE", f"/quizzes/{quiz_id}")

    def publish_quiz(self, quiz_id: int) -> Tuple[bool, Any]:
        return self._request("POST", f"/quizzes/{quiz_id}/publish")

    def unpublish_quiz(self, quiz_id: int) -> Tuple[bool, Any]:
        return self._request("POST", f"/quizzes/{quiz_id}/unpublish")

    def get_quiz_questions(self, quiz_id: int) -> Tuple[bool, Any]:
        return self._request("GET", f"/quizzes/{quiz_id}/questions")

    def add_question(self, quiz_id: int, q_data: Dict[str, Any]) -> Tuple[bool, Any]:
        return self._request("POST", f"/quizzes/{quiz_id}/questions", q_data)

    def update_question(self, question_id: int, q_data: Dict[str, Any]) -> Tuple[bool, Any]:
        return self._request("PUT", f"/questions/{question_id}", q_data)

    def delete_question(self, question_id: int) -> Tuple[bool, Any]:
        return self._request("DELETE", f"/questions/{question_id}")

    def get_students(self) -> Tuple[bool, Any]:
        return self._request("GET", "/admin/students")

    def get_admin_users(self, role: Optional[str] = None, is_active: Optional[bool] = None) -> Tuple[bool, Any]:
        params = []
        if role:
            params.append(f"role={role}")
        if is_active is not None:
            params.append(f"is_active={'true' if is_active else 'false'}")
        query = ("?" + "&".join(params)) if params else ""
        return self._request("GET", f"/admin/users{query}")

    def update_user_status(self, user_id: int, is_active: bool, reason: str = "") -> Tuple[bool, Any]:
        return self._request("PATCH", f"/admin/users/{user_id}/status", {"is_active": is_active, "reason": reason})

    def moderate_quiz(self, quiz_id: int, is_disabled: bool, reason: str = "") -> Tuple[bool, Any]:
        return self._request("PATCH", f"/admin/quizzes/{quiz_id}/moderate", {"is_disabled": is_disabled, "reason": reason})

    def get_audit_logs(self, action: Optional[str] = None, user_id: Optional[int] = None) -> Tuple[bool, Any]:
        params = []
        if action:
            params.append(f"action={action}")
        if user_id:
            params.append(f"user_id={user_id}")
        query = ("?" + "&".join(params)) if params else ""
        return self._request("GET", f"/admin/audit-logs{query}")

    def get_platform_reports(self) -> Tuple[bool, Any]:
        return self._request("GET", "/admin/platform-reports")

    def get_all_results(self) -> Tuple[bool, Any]:
        return self._request("GET", "/admin/results")

    # Organizer Operations
    def get_organizer_stats(self) -> Tuple[bool, Any]:
        return self._request("GET", "/organizer/dashboard-stats")

    def get_organizer_quizzes(self) -> Tuple[bool, Any]:
        return self._request("GET", "/organizer/quizzes")

    def get_quiz_report(self, quiz_id: int) -> Tuple[bool, Any]:
        return self._request("GET", f"/organizer/quizzes/{quiz_id}/report")

    def export_quiz_csv(self, quiz_id: int) -> Tuple[bool, Any]:
        url = f"{self.base_url}/organizer/quizzes/{quiz_id}/export-csv"
        try:
            res = self.session.get(url, headers=self._headers(), timeout=15)
            if res.status_code == 200:
                return True, res.text
            return False, res.text
        except Exception as e:
            return False, f"Failed to download CSV: {str(e)}"

    def release_results(self, quiz_id: int) -> Tuple[bool, Any]:
        return self._request("POST", f"/organizer/quizzes/{quiz_id}/release-results")

    # AI & File Generation Operations
    def generate_quiz_ai(
        self, prompt: str, num_questions: int = 5, difficulty: str = "medium", topic: Optional[str] = None, save_directly: bool = False
    ) -> Tuple[bool, Any]:
        payload = {
            "prompt": prompt,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "topic": topic,
            "save_directly": save_directly,
        }
        return self._request("POST", "/organizer/ai/generate-quiz", payload)

    def import_quiz_file(
        self, file_content: str, filename: str, num_questions: int = 5, difficulty: str = "medium", save_directly: bool = False
    ) -> Tuple[bool, Any]:
        payload = {
            "file_content": file_content,
            "filename": filename,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "save_directly": save_directly,
        }
        return self._request("POST", "/organizer/ai/import-file-quiz", payload)

    # Participant / Student Operations
    def get_published_quizzes(self) -> Tuple[bool, Any]:
        return self._request("GET", "/quizzes")

    def get_quiz_by_code(self, join_code: str) -> Tuple[bool, Any]:
        return self._request("GET", f"/quizzes/by-code/{join_code.strip().upper()}")

    def join_quiz_by_code(self, join_code: str) -> Tuple[bool, Any]:
        return self._request("POST", "/quizzes/join-by-code", {"join_code": join_code.strip().upper()})

    def get_quiz_details(self, quiz_id: int) -> Tuple[bool, Any]:
        return self._request("GET", f"/quizzes/{quiz_id}")

    def start_quiz(self, quiz_id: int) -> Tuple[bool, Any]:
        return self._request("POST", f"/attempts/quizzes/{quiz_id}/start")

    def save_answer(self, attempt_id: int, question_id: int, selected_option: Optional[str]) -> Tuple[bool, Any]:
        return self._request(
            "POST",
            f"/attempts/{attempt_id}/answers",
            {"question_id": question_id, "selected_option": selected_option},
        )

    def finish_quiz(self, attempt_id: int) -> Tuple[bool, Any]:
        return self._request("POST", f"/attempts/{attempt_id}/finish")

    def get_result(self, attempt_id: int) -> Tuple[bool, Any]:
        return self._request("GET", f"/attempts/{attempt_id}/result")

    def get_my_history(self) -> Tuple[bool, Any]:
        return self._request("GET", "/attempts/my-history")

    def get_student_dashboard_stats(self) -> Tuple[bool, Any]:
        return self._request("GET", "/attempts/my-dashboard-stats")


# Global desktop API client singleton
api_client = ApiClient()

