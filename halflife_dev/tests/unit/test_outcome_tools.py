from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager

from backend.tools import item_tools, outcome_tools
from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository


class _FakeToolContext(SimpleNamespace):
    pass


def _fake_context(user_id="user-1"):
    return _FakeToolContext(user_id=user_id)


@contextmanager
def _session_from(db_session):
    yield db_session


def test_recording_an_outcome_syncs_the_items_own_lifecycle_state(db_session):
    """Regression test: update_item_outcome only wrote to the separate
    lifecycle_assignments collection -- the item document's own
    current_lifecycle_state field (what the UI displays, what search
    filtering and Insights actually read) never changed, so a recorded
    outcome looked like it silently did nothing."""
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)), \
         patch("backend.tools.outcome_tools.tool_db_session", lambda: _session_from(db_session)):

        created = item_tools.create_item(
            _fake_context(),
            original_content="Submit tax documents by Friday",
            intent="task",
            title="Submit tax documents",
            intent_attributes={"action_text": "Submit tax documents", "due_at": "2026-09-08T00:00:00", "priority": "high"},
        )
        item_id = created["result"]["item_id"]
        assert created["result"]["lifecycle_state"] == "scheduled_for_review"

        result = outcome_tools.update_item_outcome(_fake_context(), item_id=item_id, outcome="completed")
        assert result["result"]["lifecycle_state"] == "completed"

        item = FirestoreItemRepository(db_session).get_by_id(item_id, "user-1")

    assert item.current_lifecycle_state.value == "completed"
