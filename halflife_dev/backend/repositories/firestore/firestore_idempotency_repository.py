from typing import Optional
from backend.repositories.interfaces.idempotency_repository import IdempotencyRepository
from backend.domain.schemas.idempotency import IdempotencyRecord
from backend.utils.clock import normalize_firestore_datetimes

COLLECTION = "idempotency_keys"


def _doc_id(user_id: str, idempotency_key: str, operation: str) -> str:
    # Composite natural key -> deterministic document id, so get/create/complete
    # all address the same document without needing a query.
    return f"{user_id}::{operation}::{idempotency_key}"


class FirestoreIdempotencyRepository(IdempotencyRepository):
    def __init__(self, db):
        self.db = db

    def get(self, user_id: str, idempotency_key: str, operation: str) -> Optional[IdempotencyRecord]:
        snap = self.db.collection(COLLECTION).document(_doc_id(user_id, idempotency_key, operation)).get()
        if not snap.exists:
            return None
        return self._to_domain(snap.to_dict())

    def create(self, record: IdempotencyRecord) -> IdempotencyRecord:
        doc = {
            "user_id": record.user_id,
            "idempotency_key": record.idempotency_key,
            "operation": record.operation,
            "request_hash": record.request_hash,
            "status": record.status,
            "resource_id": record.resource_id,
            "response_snapshot": record.response_snapshot,
            "created_at": record.created_at,
            "expires_at": record.expires_at,
        }
        self.db.collection(COLLECTION).document(
            _doc_id(record.user_id, record.idempotency_key, record.operation)
        ).set(doc)
        return self._to_domain(doc)

    def complete(self, user_id: str, idempotency_key: str, operation: str, resource_id: Optional[str], response_snapshot: Optional[dict]) -> IdempotencyRecord:
        doc_ref = self.db.collection(COLLECTION).document(_doc_id(user_id, idempotency_key, operation))
        snap = doc_ref.get()
        if not snap.exists:
            raise ValueError("IDEMPOTENCY_RECORD_NOT_FOUND: idempotency record not found")
        data = snap.to_dict()
        updates = {
            "status": "completed",
            "resource_id": resource_id,
            "response_snapshot": response_snapshot,
        }
        doc_ref.update(updates)
        data.update(updates)
        return self._to_domain(data)

    def _to_domain(self, data: dict) -> IdempotencyRecord:
        data = normalize_firestore_datetimes(data)
        return IdempotencyRecord(
            user_id=data["user_id"],
            idempotency_key=data["idempotency_key"],
            operation=data["operation"],
            request_hash=data["request_hash"],
            status=data["status"],
            resource_id=data.get("resource_id"),
            response_snapshot=data.get("response_snapshot"),
            created_at=data["created_at"],
            expires_at=data["expires_at"],
        )
