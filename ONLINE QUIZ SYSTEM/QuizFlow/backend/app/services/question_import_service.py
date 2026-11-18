"""Service for importing questions from various file types.

Provides two main methods:
- `extract_only(quiz_id, file_path, user_id)` – parses the file, runs the QuestionExtractor,
  and returns a list of dicts ready for preview. Each dict includes the raw fields plus
  `source: "imported"` and `creator_id`.
- `save_questions(quiz_id, payload, user_id)` – validates each preview item, creates
  `Question` ORM objects, bulk‑inserts them, and returns a summary of successes and
  failures.
"""
import os
from typing import List, Dict, Any

from app.services.question_extractor import QuestionExtractor
from app.models.question import Question
from app.database.session import SessionLocal
from sqlalchemy.exc import SQLAlchemyError

class QuestionImportService:
    @staticmethod
    def extract_only(quiz_id: int, file_path: str, user_id: int) -> List[Dict[str, Any]]:
        """Parse a file and return a preview list of question dicts.

        The function does **not** write to the DB – it is used by the preview endpoint.
        """
        # Determine mime type from extension (quick heuristic)
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        mime = mime_map.get(ext)
        if not mime:
            raise ValueError(f"Unsupported file extension: {ext}")

        from app.parsers import parse_file
        raw_text = parse_file(file_path, mime)
        extractor = QuestionExtractor(raw_text)
        extracted = extractor.extract()
        # Enrich with metadata for preview UI
        for item in extracted:
            item["source"] = "imported"
            item["creator_id"] = user_id
            item["quiz_id"] = quiz_id
        return extracted

    @staticmethod
    def save_questions(quiz_id: int, payload: List[Dict[str, Any]], user_id: int) -> Dict[str, Any]:
        """Persist a list of preview question dicts.
        Returns a summary dict: {"saved": int, "failed": int, "errors": [str]}
        """
        session = SessionLocal()
        saved = 0
        failed = 0
        errors: List[str] = []
        try:
            for idx, data in enumerate(payload, start=1):
                # Basic validation – required fields
                required = ["question_text", "option_a", "option_b", "option_c", "option_d", "correct_option"]
                if not all(k in data and data[k] for k in required):
                    failed += 1
                    errors.append(f"Item {idx} missing required fields")
                    continue
                question = Question(
                    quiz_id=quiz_id,
                    question_text=data["question_text"],
                    option_a=data["option_a"],
                    option_b=data["option_b"],
                    option_c=data["option_c"],
                    option_d=data["option_d"],
                    correct_option=data["correct_option"].upper(),
                    marks=int(data.get("marks", 1)),
                    explanation=data.get("explanation"),
                )
                # Attach creator metadata via a hidden column if needed later – for now we keep it in audit logs.
                session.add(question)
                saved += 1
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            failed += 1
            errors.append(str(e))
        finally:
            session.close()
        return {"saved": saved, "failed": failed, "errors": errors}
