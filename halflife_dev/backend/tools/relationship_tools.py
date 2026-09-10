from typing import Optional, Dict, Any
from google.adk.tools.tool_context import ToolContext

from backend.tools.db_session import tool_db_session
from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.repositories.firestore.firestore_relationship_repository import FirestoreRelationshipRepository
from backend.services.relationship_service import RelationshipService
from backend.domain.enums import RelationshipType


@as_tool_envelope("manage_relationship")
def manage_relationship(
    tool_context: ToolContext,
    action: str,
    source_item_id: Optional[str] = None,
    target_item_id: Optional[str] = None,
    relationship_type: str = "similar",
    reason: str = "",
    candidate_id: Optional[str] = None,
    relationship_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Confirm, reject, or remove a relationship between two items.

    action: 'confirm' (needs candidate_id, source_item_id, target_item_id),
    'reject' (needs candidate_id), or 'remove' (needs relationship_id).
    """
    user_id = tool_context.user_id
    with tool_db_session() as db:
        service = RelationshipService(FirestoreRelationshipRepository(db))

        if action == "confirm":
            if not candidate_id or not source_item_id or not target_item_id:
                raise ValueError("INVALID_PAYLOAD: candidate_id, source_item_id, and target_item_id are required to confirm a relationship")
            relationship = service.confirm_relationship(
                user_id, candidate_id, source_item_id, target_item_id,
                RelationshipType(relationship_type), reason or "User confirmed suggested relationship.",
            )
            return success_envelope("manage_relationship", {"relationship_id": relationship.relationship_id, "status": relationship.status})

        if action == "reject":
            if not candidate_id:
                raise ValueError("INVALID_PAYLOAD: candidate_id is required to reject a relationship")
            candidate = service.reject_candidate(user_id, candidate_id)
            return success_envelope("manage_relationship", {"candidate_id": candidate.candidate_id, "status": candidate.status})

        if action == "remove":
            if not relationship_id:
                raise ValueError("INVALID_PAYLOAD: relationship_id is required to remove a relationship")
            relationship = service.remove_relationship(user_id, relationship_id)
            return success_envelope("manage_relationship", {"relationship_id": relationship.relationship_id, "status": relationship.status})

        raise ValueError(f"INVALID_ACTION: '{action}' is not a supported relationship action")
