import uuid
from datetime import datetime
from typing import List
from backend.domain.schemas.relationships import Relationship, RelationshipCandidate
from backend.domain.enums import RelationshipType
from backend.repositories.interfaces.relationship_repository import RelationshipRepository

class RelationshipService:
    def __init__(self, relationship_repo: RelationshipRepository):
        self.relationship_repo = relationship_repo

    def suggest_candidate(self, user_id: str, source_item_id: str, target_item_id: str, suggested_type: RelationshipType, similarity_score: float = None, supporting_facts: List[str] = None) -> RelationshipCandidate:
        if source_item_id == target_item_id:
            raise ValueError("SELF_RELATIONSHIP: an item cannot relate to itself")
        candidate = RelationshipCandidate(
            candidate_id=str(uuid.uuid4()),
            user_id=user_id,
            source_item_id=source_item_id,
            target_item_id=target_item_id,
            similarity_score=similarity_score,
            suggested_type=suggested_type,
            supporting_facts=supporting_facts or [],
        )
        return self.relationship_repo.create_candidate(candidate)

    def confirm_relationship(self, user_id: str, candidate_id: str, source_item_id: str, target_item_id: str, relationship_type: RelationshipType, reason: str) -> Relationship:
        if source_item_id == target_item_id:
            raise ValueError("SELF_RELATIONSHIP: an item cannot relate to itself")
        self.relationship_repo.resolve_candidate(candidate_id, user_id, "accepted")
        relationship = Relationship(
            relationship_id=str(uuid.uuid4()),
            user_id=user_id,
            source_item_id=source_item_id,
            target_item_id=target_item_id,
            relationship_type=relationship_type,
            reason=reason,
            created_by="agent_suggestion_accepted",
        )
        return self.relationship_repo.create_relationship(relationship)

    def reject_candidate(self, user_id: str, candidate_id: str) -> RelationshipCandidate:
        return self.relationship_repo.resolve_candidate(candidate_id, user_id, "rejected")

    def remove_relationship(self, user_id: str, relationship_id: str) -> Relationship:
        return self.relationship_repo.remove_relationship(relationship_id, user_id)

    def list_for_item(self, user_id: str, item_id: str) -> List[Relationship]:
        return self.relationship_repo.list_relationships_for_item(item_id, user_id)

    def list_candidates_for_item(self, user_id: str, item_id: str) -> List[RelationshipCandidate]:
        return self.relationship_repo.list_candidates_for_item(item_id, user_id)
