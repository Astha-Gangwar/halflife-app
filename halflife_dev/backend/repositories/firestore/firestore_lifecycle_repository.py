from typing import List, Optional
from datetime import datetime
from backend.utils.clock import utcnow, normalize_firestore_datetimes
from backend.repositories.interfaces.lifecycle_repository import LifecycleRepository
from backend.domain.schemas.lifecycle import LifecycleAssignment
from backend.domain.enums import LifecycleState

COLLECTION = "lifecycle_assignments"


class FirestoreLifecycleRepository(LifecycleRepository):
    def __init__(self, db):
        self.db = db

    def upsert_assignment(self, assignment: LifecycleAssignment) -> LifecycleAssignment:
        col = self.db.collection(COLLECTION)
        existing_query = col.where("item_id", "==", assignment.item_id).where(
            "user_id", "==", assignment.user_id
        ).limit(1).stream()
        existing_snap = next(iter(existing_query), None)

        if existing_snap is not None:
            data = existing_snap.to_dict()
            updates = {
                "policy_id": assignment.policy_id,
                "policy_version": assignment.policy_version,
                "current_state": assignment.current_state.value,
                "next_review_date": assignment.next_review_date,
                "eligible_from": assignment.eligible_from,
                "cooldown_until": assignment.cooldown_until,
                "reason": assignment.reason,
                "updated_at": utcnow(),
                "version": data.get("version", 1) + 1,
            }
            existing_snap.reference.update(updates)
            data.update(updates)
            return self._to_domain(data)
        else:
            doc = {
                "assignment_id": assignment.assignment_id,
                "user_id": assignment.user_id,
                "item_id": assignment.item_id,
                "policy_id": assignment.policy_id,
                "policy_version": assignment.policy_version,
                "current_state": assignment.current_state.value,
                "next_review_date": assignment.next_review_date,
                "eligible_from": assignment.eligible_from,
                "cooldown_until": assignment.cooldown_until,
                "reason": assignment.reason,
                "created_at": assignment.created_at,
                "updated_at": assignment.updated_at,
                "version": assignment.version,
            }
            col.document(assignment.assignment_id).set(doc)
            return self._to_domain(doc)

    def get_by_item_id(self, item_id: str, user_id: str) -> Optional[LifecycleAssignment]:
        query = self.db.collection(COLLECTION).where("item_id", "==", item_id).where(
            "user_id", "==", user_id
        ).limit(1).stream()
        snap = next(iter(query), None)
        if snap is None:
            return None
        return self._to_domain(snap.to_dict())

    def get_revisit_candidates(self, user_id: str, limit: int = 10) -> List[LifecycleAssignment]:
        query = self.db.collection(COLLECTION).where("user_id", "==", user_id).where(
            "current_state", "==", LifecycleState.SCHEDULED_FOR_REVIEW.value
        ).limit(limit).stream()
        return [self._to_domain(s.to_dict()) for s in query]

    def _to_domain(self, data: dict) -> LifecycleAssignment:
        data = normalize_firestore_datetimes(data)
        return LifecycleAssignment(
            assignment_id=data["assignment_id"],
            user_id=data["user_id"],
            item_id=data["item_id"],
            policy_id=data["policy_id"],
            policy_version=data["policy_version"],
            current_state=LifecycleState(data["current_state"]),
            next_review_date=data.get("next_review_date"),
            eligible_from=data.get("eligible_from"),
            cooldown_until=data.get("cooldown_until"),
            reason=data.get("reason"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            version=data["version"],
        )
