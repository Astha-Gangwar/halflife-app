from datetime import timedelta
from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
from backend.services.insights_service import InsightsService
from backend.utils.clock import utcnow


def _put_item(db_session, item_id, category, lifecycle_state, created_at, status="active"):
    db_session.collection("items").document(item_id).set({
        "item_id": item_id,
        "user_id": "user-1",
        "original_content": "content",
        "content_format": "text",
        "user_title": None,
        "user_note": None,
        "approved_title": item_id,
        "approved_summary": None,
        "intent_type": "general_note",
        "category": category,
        "tags": [],
        "intent_attributes": {},
        "approved_analysis_id": "an-1",
        "status": status,
        "current_lifecycle_state": lifecycle_state,
        "version": 1,
        "created_at": created_at,
        "updated_at": created_at,
        "archived_at": None,
        "deleted_at": None,
    })


def test_summary_computes_consumption_and_backlog(db_session):
    now = utcnow()
    _put_item(db_session, "i1", "recipes", "completed", now)
    _put_item(db_session, "i2", "recipes", "saved", now)
    _put_item(db_session, "i3", "ideas", "saved", now - timedelta(days=20))  # stale
    _put_item(db_session, "i4", "ideas", "dismissed", now)
    _put_item(db_session, "i5", "recipes", "not_relevant", now, status="deleted")  # excluded

    service = InsightsService(FirestoreItemRepository(db_session))
    summary = service.get_summary("user-1")

    assert summary["total_saved"] == 4  # deleted item excluded
    assert summary["consumption_rate"] == 50  # i1, i4 acted on out of 4
    assert summary["active_backlog"] == 2  # i2, i3
    assert summary["stale_backlog"] == 1  # i3
    assert summary["revisit_success_rate"] == 50  # 1 positive (i1) vs 1 negative (i4)

    categories = {row["category"]: row for row in summary["category_performance"]}
    assert categories["recipes"]["total"] == 2
    assert categories["recipes"]["acted_on_rate"] == 50
    assert categories["ideas"]["total"] == 2
    assert categories["ideas"]["acted_on_rate"] == 50


def test_summary_handles_empty_account(db_session):
    service = InsightsService(FirestoreItemRepository(db_session))
    summary = service.get_summary("user-with-nothing")

    assert summary["total_saved"] == 0
    assert summary["consumption_rate"] == 0
    assert summary["revisit_success_rate"] is None
    assert summary["category_performance"] == []
    assert "Nothing saved yet" in summary["behavior_insights"][0]
