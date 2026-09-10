from typing import List, Optional
from backend.repositories.interfaces.resurfacing_repository import ResurfacingRepository
from backend.domain.schemas.lifecycle import ResurfacingCandidate
from backend.domain.enums import ResurfacingStatus
from backend.utils.clock import normalize_firestore_datetimes

COLLECTION = "resurfacing_candidates"


class FirestoreResurfacingRepository(ResurfacingRepository):
    def __init__(self, db):
        self.db = db

    def create_candidate(self, candidate: ResurfacingCandidate) -> ResurfacingCandidate:
        doc = {
            "resurfacing_id": candidate.resurfacing_id,
            "user_id": candidate.user_id,
            "item_id": candidate.item_id,
            "assignment_id": candidate.assignment_id,
            "status": candidate.status.value,
            "eligibility_reason_code": candidate.eligibility_reason_code,
            "supporting_facts": dict(candidate.supporting_facts),
            "rank_score": candidate.rank_score,
            "rank_factors": dict(candidate.rank_factors),
            "eligible_at": candidate.eligible_at,
            "selected_at": candidate.selected_at,
            "presented_at": candidate.presented_at,
            "expires_at": candidate.expires_at,
            "created_at": candidate.created_at,
        }
        self.db.collection(COLLECTION).document(candidate.resurfacing_id).set(doc)
        return self._to_domain(doc)

    def get_by_id(self, resurfacing_id: str, user_id: str) -> Optional[ResurfacingCandidate]:
        snap = self.db.collection(COLLECTION).document(resurfacing_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict()
        if data.get("user_id") != user_id:
            return None
        return self._to_domain(data)

    def update_status(self, resurfacing_id: str, user_id: str, status: str, presented_at=None) -> ResurfacingCandidate:
        doc_ref = self.db.collection(COLLECTION).document(resurfacing_id)
        snap = doc_ref.get()
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("CANDIDATE_NOT_FOUND: resurfacing candidate not found or unauthorized")
        data = snap.to_dict()
        updates = {"status": status}
        if presented_at is not None:
            updates["presented_at"] = presented_at
        doc_ref.update(updates)
        data.update(updates)
        return self._to_domain(data)

    def list_by_status(self, user_id: str, status: str, limit: int = 50) -> List[ResurfacingCandidate]:
        query = self.db.collection(COLLECTION).where("user_id", "==", user_id).where(
            "status", "==", status
        ).limit(limit).stream()
        return [self._to_domain(s.to_dict()) for s in query]

    def _to_domain(self, data: dict) -> ResurfacingCandidate:
        data = normalize_firestore_datetimes(data)
        return ResurfacingCandidate(
            resurfacing_id=data["resurfacing_id"],
            user_id=data["user_id"],
            item_id=data["item_id"],
            assignment_id=data["assignment_id"],
            status=ResurfacingStatus(data["status"]),
            eligibility_reason_code=data["eligibility_reason_code"],
            supporting_facts=data.get("supporting_facts") or {},
            rank_score=data.get("rank_score"),
            rank_factors=data.get("rank_factors") or {},
            eligible_at=data["eligible_at"],
            selected_at=data.get("selected_at"),
            presented_at=data.get("presented_at"),
            expires_at=data.get("expires_at"),
            created_at=data["created_at"],
        )
