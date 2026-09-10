"""Standard tool response envelope (Batch 5 §4) and error mapping (§20).

Every agent-facing tool returns this shape so the agent can reason about
success/failure uniformly and never has to guess at ad-hoc dict keys.
"""
import uuid
import functools
from typing import Any, Optional, List, Dict, Callable

_ERROR_CATALOGUE = {
    "INVALID_PAYLOAD": ("validation", False),
    "ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE": ("not_found", False),
    "VERSION_CONFLICT": ("conflict", False),
    "IDEMPOTENCY_CONFLICT": ("conflict", False),
    "INVALID_STATE_TRANSITION": ("business_rule", False),
    "INVALID_ACTION": ("validation", False),
    "SELF_RELATIONSHIP": ("validation", False),
    "DUPLICATE_RELATIONSHIP": ("conflict", False),
    "DUPLICATE_COLLECTION_NAME": ("conflict", False),
    "UNSUPPORTED_MEDIA_TYPE": ("validation", False),
    "FILE_TOO_LARGE": ("validation", False),
    "REQUIRED_PREFERENCE_MISSING": ("business_rule", False),
    "NO_APPLICABLE_POLICY": ("business_rule", False),
    "INSUFFICIENT_COMPARABLE_DATA": ("business_rule", False),
    "INVALID_OUTCOME": ("validation", False),
    "STORAGE_UNAVAILABLE": ("dependency", True),
    "ANALYSIS_NOT_FOUND_OR_NOT_ACCESSIBLE": ("not_found", False),
    "ATTACHMENT_NOT_FOUND_OR_NOT_ACCESSIBLE": ("not_found", False),
    "COLLECTION_NOT_FOUND_OR_NOT_ACCESSIBLE": ("not_found", False),
    "RELATIONSHIP_NOT_FOUND_OR_NOT_ACCESSIBLE": ("not_found", False),
    "CANDIDATE_NOT_FOUND": ("not_found", False),
    "IDEMPOTENCY_RECORD_NOT_FOUND": ("not_found", False),
    "NO_ACTIVE_LIFECYCLE_ASSIGNMENT": ("business_rule", False),
}


def success_envelope(
    operation: str,
    result: Any,
    correlation_id: Optional[str] = None,
    resource_version: Optional[int] = None,
    next_action: Optional[str] = None,
    events_recorded: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "status": "success",
        "operation": operation,
        "result": result,
        "error": None,
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "resource_version": resource_version,
        "next_action": next_action,
        "events_recorded": events_recorded or [],
        "warnings": warnings or [],
    }


def error_envelope(operation: str, message: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
    code = message.split(":", 1)[0].strip() if ":" in message else "INTERNAL_ERROR"
    if not code.isupper() or code not in _ERROR_CATALOGUE:
        code = code if code in _ERROR_CATALOGUE else "INTERNAL_ERROR"
    category, retryable = _ERROR_CATALOGUE.get(code, ("internal", False))
    return {
        "status": "error",
        "operation": operation,
        "result": None,
        "error": {
            "code": code,
            "category": category,
            "message": message,
            "field_path": None,
            "retryable": retryable,
            "details": {},
        },
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "resource_version": None,
        "next_action": None,
        "events_recorded": [],
        "warnings": [],
    }


def as_tool_envelope(operation: str) -> Callable:
    """Decorator: wraps a tool body so any ValueError becomes a safe error
    envelope instead of propagating a raw traceback to the agent (Batch 5
    §20: the model never sees a stack trace)."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                return error_envelope(operation, str(e))
        return wrapper
    return decorator
