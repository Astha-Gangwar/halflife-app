from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager

from backend.tools import item_tools, lifecycle_tools


class _FakeToolContext(SimpleNamespace):
    pass


def _fake_context(user_id="user-1"):
    return _FakeToolContext(user_id=user_id)


@contextmanager
def _session_from(db_session):
    yield db_session


def test_standalone_assign_lifecycle_preserves_reference_category(db_session):
    """Regression test: the agent commonly calls create_item, then the
    standalone assign_lifecycle tool right after (e.g. trigger_reason=
    "item_approved"). That second call must not silently drop the item's
    reference-category override and re-run it through the generic
    per-intent decay policy — it previously did, because assign_lifecycle
    (lifecycle_tools.py) fetched the item but never passed item.category
    through to LifecycleService.assign_lifecycle."""
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)), \
         patch("backend.tools.lifecycle_tools.tool_db_session", lambda: _session_from(db_session)):

        created = item_tools.create_item(
            _fake_context(),
            original_content="Packing checklist: passport, charger, adapter, meds",
            intent="task",
            title="Packing checklist",
            category="checklist",
            intent_attributes={"action_text": "pack", "priority": "high", "due_at": "2026-09-08T00:00:00"},
        )
        item_id = created["result"]["item_id"]
        assert created["result"]["lifecycle_state"] == "saved"

        reassigned = lifecycle_tools.assign_lifecycle(_fake_context(), item_id=item_id)

    assert reassigned["result"]["current_state"] == "saved"
    assert reassigned["result"]["next_review_date"] is None
    assert "REFERENCE_CATEGORY" in reassigned["result"]["reason"]


def test_standalone_assign_lifecycle_still_applies_normal_task_policy(db_session):
    """Sanity check that the fix doesn't over-apply: an ordinary task with
    no reference category still gets the normal due-date-driven policy on
    a standalone re-assignment."""
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)), \
         patch("backend.tools.lifecycle_tools.tool_db_session", lambda: _session_from(db_session)):

        created = item_tools.create_item(
            _fake_context(),
            original_content="Submit tax documents by Friday",
            intent="task",
            title="Submit tax documents",
            intent_attributes={"action_text": "Submit tax documents", "due_at": "2026-09-08T00:00:00", "priority": "high"},
        )
        item_id = created["result"]["item_id"]

        reassigned = lifecycle_tools.assign_lifecycle(_fake_context(), item_id=item_id)

    assert reassigned["result"]["current_state"] == "scheduled_for_review"
    assert reassigned["result"]["next_review_date"] is not None
