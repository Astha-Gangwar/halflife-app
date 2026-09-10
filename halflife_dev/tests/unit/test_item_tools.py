from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager

from backend.tools import item_tools


class _FakeToolContext(SimpleNamespace):
    pass


def _fake_context(user_id="user-1"):
    return _FakeToolContext(user_id=user_id)


@contextmanager
def _session_from(db_session):
    yield db_session


def test_create_item_tool_persists_and_assigns_lifecycle(db_session):
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        result = item_tools.create_item(
            _fake_context(),
            original_content="Paneer tikka with curd and spices",
            intent="recipe",
            title="Paneer Tikka",
        )

    assert result["status"] == "success"
    assert result["result"]["approved_title"] == "Paneer Tikka"
    assert "lifecycle_state" in result["result"]


def test_get_item_tool_not_found_returns_error_envelope(db_session):
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        result = item_tools.get_item(_fake_context(), item_id="does-not-exist")

    assert result["status"] == "error"
    assert result["error"]["code"] == "ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE"


def test_get_item_tool_scoped_to_owner(db_session):
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        created = item_tools.create_item(
            _fake_context("user-1"), original_content="note", intent="general_note",
        )
        item_id = created["result"]["item_id"]

        result = item_tools.get_item(_fake_context("user-2"), item_id=item_id)

    assert result["status"] == "error"
    assert result["error"]["code"] == "ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE"
