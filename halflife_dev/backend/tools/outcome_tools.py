from typing import Optional, Dict, Any
from google.adk.tools.tool_context import ToolContext

from backend.tools.db_session import tool_db_session
from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.repositories.firestore.firestore_lifecycle_repository import FirestoreLifecycleRepository
from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
from backend.repositories.firestore.firestore_feedback_repository import FirestoreFeedbackRepository
from backend.services.lifecycle_service import LifecycleService
from backend.services.item_service import ItemService
from backend.services.feedback_service import FeedbackService
from backend.domain.enums import OutcomeType


@as_tool_envelope("update_item_outcome")
def update_item_outcome(
    tool_context: ToolContext,
    item_id: str,
    outcome: str,
    remind_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate and apply a user-selected outcome: tried, completed,
    dismissed, modified, not_relevant, remind_later, archived, or restored."""
    user_id = tool_context.user_id
    try:
        outcome_enum = OutcomeType(outcome)
    except ValueError:
        raise ValueError(f"INVALID_OUTCOME: '{outcome}' is not a supported outcome")

    remind_at_dt = None
    if remind_at:
        from datetime import datetime
        remind_at_dt = datetime.fromisoformat(remind_at)

    with tool_db_session() as db:
        item_service = ItemService(FirestoreItemRepository(db))
        item = item_service.get_item(item_id, user_id)
        if item is None:
            raise ValueError("ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE: item not found")

        assignment = LifecycleService(FirestoreLifecycleRepository(db)).update_item_outcome(
            item_id, user_id, item.intent_type, outcome_enum,
            remind_at=remind_at_dt, intent_attributes=item.intent_attributes,
            category=item.category,
        )
        item_service.sync_lifecycle_state(item_id, user_id, assignment.current_state)

    return success_envelope("update_item_outcome", {
        "item_id": item_id,
        "lifecycle_state": assignment.current_state.value,
        "next_review_date": assignment.next_review_date.isoformat() if assignment.next_review_date else None,
    }, resource_version=assignment.version)


@as_tool_envelope("record_feedback")
def record_feedback(
    tool_context: ToolContext,
    item_id: str,
    feedback_type: str,
    selected_value: str,
    comment: Optional[str] = None,
    resurfacing_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Store a structured user response to a supported feedback question."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        feedback = FeedbackService(FirestoreFeedbackRepository(db)).record_feedback(
            user_id, item_id, feedback_type, selected_value, comment=comment, resurfacing_id=resurfacing_id,
        )

    return success_envelope("record_feedback", {"feedback_id": feedback.feedback_id})
