from typing import Optional, Dict, Any
from google.adk.tools.tool_context import ToolContext

from backend.tools.db_session import tool_db_session
from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.repositories.firestore.firestore_lifecycle_repository import FirestoreLifecycleRepository
from backend.repositories.firestore.firestore_resurfacing_repository import FirestoreResurfacingRepository
from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
from backend.services.lifecycle_service import LifecycleService
from backend.services.resurfacing_service import ResurfacingService
from backend.services.item_service import ItemService
from backend.domain.enums import IntentType


@as_tool_envelope("assign_lifecycle")
def assign_lifecycle(tool_context: ToolContext, item_id: str, trigger_reason: str = "item_approved") -> Dict[str, Any]:
    """(Re)assign the deterministic lifecycle policy for an item, e.g. after
    approval, a material edit, or a preference change."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        item_service = ItemService(FirestoreItemRepository(db))
        item = item_service.get_item(item_id, user_id)
        if item is None:
            raise ValueError("ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE: item not found")

        assignment = LifecycleService(FirestoreLifecycleRepository(db)).assign_lifecycle(
            item_id=item_id, user_id=user_id, intent=item.intent_type,
            preferences={}, intent_attributes=item.intent_attributes,
            category=item.category,
        )
        item_service.sync_lifecycle_state(item_id, user_id, assignment.current_state)

    return success_envelope("assign_lifecycle", {
        "assignment_id": assignment.assignment_id,
        "current_state": assignment.current_state.value,
        "next_review_date": assignment.next_review_date.isoformat() if assignment.next_review_date else None,
        "reason": assignment.reason,
    }, resource_version=assignment.version)


@as_tool_envelope("get_revisit_candidates")
def get_revisit_candidates(tool_context: ToolContext, limit: int = 10) -> Dict[str, Any]:
    """Retrieve, filter, and rank eligible memories for revisiting."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        service = ResurfacingService(FirestoreLifecycleRepository(db), FirestoreResurfacingRepository(db))
        candidates = service.get_revisit_candidates(user_id, limit=limit)

    return success_envelope("get_revisit_candidates", {
        "candidates": [
            {
                "resurfacing_id": c.resurfacing_id,
                "item_id": c.item_id,
                "eligibility_reason_code": c.eligibility_reason_code,
                "supporting_facts": c.supporting_facts,
                "rank_score": c.rank_score,
            }
            for c in candidates
        ]
    })


@as_tool_envelope("record_resurfacing")
def record_resurfacing(tool_context: ToolContext, resurfacing_id: str) -> Dict[str, Any]:
    """Record that the web application actually presented a candidate to the user."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        service = ResurfacingService(FirestoreLifecycleRepository(db), FirestoreResurfacingRepository(db))
        candidate = service.record_resurfacing(resurfacing_id, user_id)

    return success_envelope("record_resurfacing", {"resurfacing_id": candidate.resurfacing_id, "status": candidate.status.value})
