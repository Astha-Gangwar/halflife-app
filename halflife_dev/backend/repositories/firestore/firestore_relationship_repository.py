from typing import List
from datetime import datetime
from backend.utils.clock import utcnow, normalize_firestore_datetimes
from backend.repositories.interfaces.relationship_repository import RelationshipRepository
from backend.domain.schemas.relationships import Relationship, RelationshipCandidate
from backend.domain.enums import RelationshipType

CANDIDATES_COLLECTION = "relationship_candidates"
RELATIONSHIPS_COLLECTION = "relationships"


class FirestoreRelationshipRepository(RelationshipRepository):
    def __init__(self, db):
        self.db = db

    def create_candidate(self, candidate: RelationshipCandidate) -> RelationshipCandidate:
        doc = {
            "candidate_id": candidate.candidate_id,
            "user_id": candidate.user_id,
            "source_item_id": candidate.source_item_id,
            "target_item_id": candidate.target_item_id,
            "similarity_score": candidate.similarity_score,
            "suggested_type": candidate.suggested_type.value,
            "supporting_facts": list(candidate.supporting_facts),
            "status": candidate.status,
            "created_at": candidate.created_at,
            "resolved_at": candidate.resolved_at,
        }
        self.db.collection(CANDIDATES_COLLECTION).document(candidate.candidate_id).set(doc)
        return self._candidate_to_domain(doc)

    def list_candidates_for_item(self, item_id: str, user_id: str) -> List[RelationshipCandidate]:
        query = self.db.collection(CANDIDATES_COLLECTION).where(
            "source_item_id", "==", item_id
        ).where("user_id", "==", user_id).stream()
        return [self._candidate_to_domain(s.to_dict()) for s in query]

    def resolve_candidate(self, candidate_id: str, user_id: str, status: str) -> RelationshipCandidate:
        doc_ref = self.db.collection(CANDIDATES_COLLECTION).document(candidate_id)
        snap = doc_ref.get()
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("CANDIDATE_NOT_FOUND: relationship candidate not found or unauthorized")
        data = snap.to_dict()
        updates = {"status": status, "resolved_at": utcnow()}
        doc_ref.update(updates)
        data.update(updates)
        return self._candidate_to_domain(data)

    def create_relationship(self, relationship: Relationship) -> Relationship:
        doc = {
            "relationship_id": relationship.relationship_id,
            "user_id": relationship.user_id,
            "source_item_id": relationship.source_item_id,
            "target_item_id": relationship.target_item_id,
            "relationship_type": relationship.relationship_type.value,
            "reason": relationship.reason,
            "created_by": relationship.created_by,
            "status": relationship.status,
            "created_at": relationship.created_at,
            "removed_at": relationship.removed_at,
            "version": relationship.version,
        }
        self.db.collection(RELATIONSHIPS_COLLECTION).document(relationship.relationship_id).set(doc)
        return self._relationship_to_domain(doc)

    def list_relationships_for_item(self, item_id: str, user_id: str) -> List[Relationship]:
        col = self.db.collection(RELATIONSHIPS_COLLECTION)
        # Firestore doesn't support OR across fields in one query the same
        # way SQL does, so this mirrors the sqlite semantics
        # (source_item_id == item_id OR target_item_id == item_id) with two
        # queries merged client-side.
        as_source = col.where("source_item_id", "==", item_id).where(
            "user_id", "==", user_id
        ).where("status", "==", "confirmed").stream()
        as_target = col.where("target_item_id", "==", item_id).where(
            "user_id", "==", user_id
        ).where("status", "==", "confirmed").stream()

        seen = {}
        for snap in list(as_source) + list(as_target):
            data = snap.to_dict()
            seen[data["relationship_id"]] = data
        return [self._relationship_to_domain(d) for d in seen.values()]

    def remove_relationship(self, relationship_id: str, user_id: str) -> Relationship:
        doc_ref = self.db.collection(RELATIONSHIPS_COLLECTION).document(relationship_id)
        snap = doc_ref.get()
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("RELATIONSHIP_NOT_FOUND_OR_NOT_ACCESSIBLE: relationship not found or unauthorized")
        data = snap.to_dict()
        updates = {
            "status": "removed",
            "removed_at": utcnow(),
            "version": data.get("version", 1) + 1,
        }
        doc_ref.update(updates)
        data.update(updates)
        return self._relationship_to_domain(data)

    def _candidate_to_domain(self, data: dict) -> RelationshipCandidate:
        data = normalize_firestore_datetimes(data)
        return RelationshipCandidate(
            candidate_id=data["candidate_id"],
            user_id=data["user_id"],
            source_item_id=data["source_item_id"],
            target_item_id=data["target_item_id"],
            similarity_score=data.get("similarity_score"),
            suggested_type=RelationshipType(data["suggested_type"]),
            supporting_facts=data.get("supporting_facts") or [],
            status=data["status"],
            created_at=data["created_at"],
            resolved_at=data.get("resolved_at"),
        )

    def _relationship_to_domain(self, data: dict) -> Relationship:
        data = normalize_firestore_datetimes(data)
        return Relationship(
            relationship_id=data["relationship_id"],
            user_id=data["user_id"],
            source_item_id=data["source_item_id"],
            target_item_id=data["target_item_id"],
            relationship_type=RelationshipType(data["relationship_type"]),
            reason=data["reason"],
            created_by=data["created_by"],
            status=data["status"],
            created_at=data["created_at"],
            removed_at=data.get("removed_at"),
            version=data["version"],
        )
