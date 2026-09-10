from abc import ABC, abstractmethod
from typing import List, Optional
from backend.domain.schemas.relationships import Relationship, RelationshipCandidate

class RelationshipRepository(ABC):
    @abstractmethod
    def create_candidate(self, candidate: RelationshipCandidate) -> RelationshipCandidate:
        pass

    @abstractmethod
    def list_candidates_for_item(self, item_id: str, user_id: str) -> List[RelationshipCandidate]:
        pass

    @abstractmethod
    def resolve_candidate(self, candidate_id: str, user_id: str, status: str) -> RelationshipCandidate:
        pass

    @abstractmethod
    def create_relationship(self, relationship: Relationship) -> Relationship:
        pass

    @abstractmethod
    def list_relationships_for_item(self, item_id: str, user_id: str) -> List[Relationship]:
        pass

    @abstractmethod
    def remove_relationship(self, relationship_id: str, user_id: str) -> Relationship:
        pass
