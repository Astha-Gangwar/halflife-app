import hashlib
import json
from datetime import datetime, timedelta
from backend.utils.clock import utcnow
from typing import Optional, Dict, Any
from backend.domain.schemas.idempotency import IdempotencyRecord
from backend.repositories.interfaces.idempotency_repository import IdempotencyRepository

IDEMPOTENCY_RETENTION_HOURS = 24


def hash_request(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


class IdempotencyConflict(Exception):
    """Same key, different request payload (Batch 5 IDEM-003 / IDEMPOTENCY_CONFLICT)."""


def apply_idempotency(
    repo: IdempotencyRepository,
    user_id: str,
    idempotency_key: Optional[str],
    operation: str,
    request_payload: Dict[str, Any],
):
    """Idempotency guard for a state-changing operation (Batch 5 §19).

    Usage:
        existing = apply_idempotency(repo, user_id, key, "create_item", payload)
        if existing is not None:
            return existing.response_snapshot  # replay prior result
        # ... perform the real write ...
        repo.complete(user_id, key, "create_item", resource_id, response_snapshot)

    Returns the existing completed record to replay if the key was already
    used with an equivalent payload; returns None when the caller should
    proceed with a fresh write. Raises IdempotencyConflict if the same key
    was used with a materially different payload.
    """
    if not idempotency_key:
        return None

    request_hash = hash_request(request_payload)
    existing = repo.get(user_id, idempotency_key, operation)
    if existing is None:
        repo.create(IdempotencyRecord(
            user_id=user_id,
            idempotency_key=idempotency_key,
            operation=operation,
            request_hash=request_hash,
            expires_at=utcnow() + timedelta(hours=IDEMPOTENCY_RETENTION_HOURS),
        ))
        return None

    if existing.request_hash != request_hash:
        raise IdempotencyConflict(f"IDEMPOTENCY_CONFLICT: key '{idempotency_key}' already used with a different request")

    return existing
