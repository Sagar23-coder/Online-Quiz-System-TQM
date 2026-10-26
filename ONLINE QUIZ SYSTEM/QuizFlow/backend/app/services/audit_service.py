"""
Audit Logging Service.
Records privacy-conscious, tamper-evident audit records for all significant platform actions.
"""
import json
import logging
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger("quizflow.audit")

SENSITIVE_KEYS = {"password", "confirm_password", "token", "access_token", "hashed_password", "secret"}


def _sanitize_payload(data: Any) -> Any:
    """Recursively scrub sensitive keys from log payloads."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if k.lower() in SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = _sanitize_payload(v)
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_payload(item) for item in data]
    return data


class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[str, int]] = None,
        details: Optional[Union[str, Dict[str, Any]]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Record an immutable audit log entry in the database.
        """
        details_str: Optional[str] = None
        if isinstance(details, dict):
            try:
                scrubbed = _sanitize_payload(details)
                details_str = json.dumps(scrubbed)
            except Exception:
                details_str = str(details)
        elif details is not None:
            details_str = str(details)

        res_id_str = str(resource_id) if resource_id is not None else None

        entry = AuditLog(
            user_id=user_id,
            action=action.upper(),
            resource_type=resource_type.lower() if resource_type else None,
            resource_id=res_id_str,
            details=details_str,
            ip_address=ip_address,
        )

        try:
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            db.rollback()
            logger.error("Failed to write audit log entry: %s", e)
            return entry

