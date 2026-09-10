from typing import List, Optional, Dict, Any
from google.adk.tools.tool_context import ToolContext

from backend.tools.db_session import tool_db_session
from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.repositories.firestore.firestore_event_repository import FirestoreEventRepository
from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
from backend.services.event_service import EventService
from backend.services.item_service import ItemService


@as_tool_envelope("get_item_history")
def get_item_history(tool_context: ToolContext, item_id: str, limit: int = 50) -> Dict[str, Any]:
    """Retrieve an item's recorded events (safe metadata only, no hidden reasoning)."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        events = EventService(FirestoreEventRepository(db)).list_for_item(user_id, item_id, limit=limit)

    return success_envelope("get_item_history", {
        "events": [
            {
                "event_type": e.event_type,
                "occurred_at": e.occurred_at.isoformat(),
                "status": e.status.value,
                "metadata": e.metadata,
            }
            for e in events
        ]
    })


def _normalize_metric(attrs: Dict[str, Any], key: str) -> Optional[float]:
    value = attrs.get(key)
    return float(value) if value is not None else None


@as_tool_envelope("compare_activity_history")
def compare_activity_history(tool_context: ToolContext, current_item_id: str, comparison_item_ids: List[str]) -> Dict[str, Any]:
    """Calculate deterministic factual differences between an activity log
    and one or more prior comparable activity logs. No health/training advice."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        item_service = ItemService(FirestoreItemRepository(db))
        current = item_service.get_item(current_item_id, user_id)
        if current is None:
            raise ValueError("ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE: current item not found")

        comparisons = []
        for comp_id in comparison_item_ids:
            comp_item = item_service.get_item(comp_id, user_id)
            if comp_item is None or comp_item.intent_type != current.intent_type:
                continue
            if comp_item.intent_attributes.get("activity_type") != current.intent_attributes.get("activity_type"):
                continue
            comparisons.append(comp_item)

    if not comparisons:
        raise ValueError("INSUFFICIENT_COMPARABLE_DATA: no comparable activity logs found")

    metrics = ["duration_minutes", "distance_km"]
    differences = []
    for comp_item in comparisons:
        entry = {"item_id": comp_item.item_id, "differences": {}}
        for metric in metrics:
            current_value = _normalize_metric(current.intent_attributes, metric)
            comp_value = _normalize_metric(comp_item.intent_attributes, metric)
            if current_value is None or comp_value is None:
                entry["differences"][metric] = None
            else:
                entry["differences"][metric] = round(current_value - comp_value, 2)
        differences.append(entry)

    return success_envelope("compare_activity_history", {"current_item_id": current_item_id, "comparisons": differences})
