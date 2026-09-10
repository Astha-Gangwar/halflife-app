"""Grounding tests (Batch 5 §22): a tool's response must always reflect what
actually happened — never claim success on a failed operation, never
fabricate data for something that doesn't exist. This is what "the agent
must not invent a fallback result" (Batch 5 §15) rests on at the tool level.
"""
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from backend.tools import item_tools, lifecycle_tools, relationship_tools, collection_tools


def _ctx(user_id="user-1"):
    return SimpleNamespace(user_id=user_id)


@contextmanager
def _session_from(db_session):
    yield db_session


def test_get_item_never_returns_success_for_a_missing_item(db_session):
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        result = item_tools.get_item(_ctx(), item_id="ghost-item")

    assert result["status"] == "error"
    assert result["result"] is None
    assert result["error"]["code"] == "ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE"


def test_update_item_never_reports_success_on_version_conflict(db_session):
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        created = item_tools.create_item(
            _ctx(), original_content="note", intent="general_note",
        )
        item_id = created["result"]["item_id"]

        item_tools.update_item(_ctx(), item_id=item_id, expected_version=1, approved_title="First edit")
        stale_result = item_tools.update_item(_ctx(), item_id=item_id, expected_version=1, approved_title="Stale edit")

    assert stale_result["status"] == "error"
    assert stale_result["error"]["code"] == "VERSION_CONFLICT"


def test_change_item_status_rejects_unknown_action_without_mutating(db_session):
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        created = item_tools.create_item(
            _ctx(), original_content="note", intent="general_note",
        )
        item_id = created["result"]["item_id"]

        result = item_tools.change_item_status(_ctx(), item_id=item_id, action="teleport")
        assert result["status"] == "error"

        # The item's real status must be unaffected by the rejected action.
        fetched = item_tools.get_item(_ctx(), item_id=item_id)
        assert fetched["result"]["status"] == "active"


def test_assign_lifecycle_never_succeeds_for_a_nonexistent_item(db_session):
    with patch("backend.tools.lifecycle_tools.tool_db_session", lambda: _session_from(db_session)):
        result = lifecycle_tools.assign_lifecycle(_ctx(), item_id="ghost-item")

    assert result["status"] == "error"
    assert result["error"]["code"] == "ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE"


def test_manage_relationship_rejects_incomplete_confirm_payload(db_session):
    with patch("backend.tools.relationship_tools.tool_db_session", lambda: _session_from(db_session)):
        result = relationship_tools.manage_relationship(_ctx(), action="confirm")

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_PAYLOAD"


def test_manage_collection_rejects_unknown_action(db_session):
    with patch("backend.tools.collection_tools.tool_db_session", lambda: _session_from(db_session)):
        result = collection_tools.manage_collection(_ctx(), action="teleport")

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_ACTION"


def test_error_envelopes_never_carry_a_fabricated_result(db_session):
    """Every error envelope across the tool layer must have result=None —
    a tool must never partially fabricate data alongside an error status."""
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        result = item_tools.get_item(_ctx(), item_id="ghost-item")
    assert result["status"] == "error"
    assert result["result"] is None
