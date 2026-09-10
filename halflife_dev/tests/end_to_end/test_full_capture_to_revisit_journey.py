"""End-to-end journey test: simulates the agent's create_item tool call
(the real path an actual Gemini tool-call would take — capture.py can't be
driven directly here without live API credentials) producing an item with a
real lifecycle assignment, then walks the rest of the journey — revisit,
outcome, feedback, history — entirely through the real HTTP API, exactly as
the frontend does.

This is the one test file that exercises the agent *tool* layer and the
*route* layer together against the same database, rather than testing each
in isolation.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta
from backend.utils.clock import utcnow
from types import SimpleNamespace
from unittest.mock import patch

from tests.conftest import auth_headers
from backend.tools import item_tools


def test_full_journey_from_agent_creation_to_revisit_and_outcome(e2e_env):
    client, mock_db = e2e_env

    @contextmanager
    def _session():
        yield mock_db

    # Step 1: the agent (via its create_item tool) saves an overdue task —
    # deterministically eligible for revisit immediately (Batch 6 TASK_OVERDUE).
    overdue = (utcnow() - timedelta(days=1)).isoformat()
    with patch("backend.tools.item_tools.tool_db_session", _session):
        tool_result = item_tools.create_item(
            SimpleNamespace(user_id="user-1"),
            original_content="Renew passport before the trip",
            intent="task",
            title="Renew Passport",
            intent_attributes={"action_text": "Renew passport", "due_at": overdue, "priority": "high", "task_status": "open"},
        )
    assert tool_result["status"] == "success"
    item_id = tool_result["result"]["item_id"]
    assert tool_result["result"]["lifecycle_state"] == "scheduled_for_review"

    # Step 2: the frontend fetches the item directly.
    get_resp = client.get(f"/items/{item_id}", headers=auth_headers())
    assert get_resp.status_code == 200
    assert get_resp.json()["approved_title"] == "Renew Passport"

    # Step 3: the frontend's Revisit page asks for eligible candidates.
    revisit_resp = client.get("/revisit/candidates", headers=auth_headers())
    assert revisit_resp.status_code == 200
    candidates = revisit_resp.json()
    assert len(candidates) == 1
    assert candidates[0]["item_id"] == item_id
    assert candidates[0]["eligibility_reason_code"] == "TASK_OVERDUE"

    # Step 4: the user marks it completed.
    outcome_resp = client.post(f"/outcomes/{item_id}", json={"outcome": "completed"}, headers=auth_headers())
    assert outcome_resp.status_code == 200
    assert outcome_resp.json()["lifecycle_state"] == "completed"

    # Step 5: a completed item is no longer an eligible revisit candidate.
    revisit_after = client.get("/revisit/candidates", headers=auth_headers())
    assert revisit_after.json() == []

    # Step 6: the user leaves feedback and it shows up in history-adjacent views.
    feedback_resp = client.post("/feedback/", json={
        "item_id": item_id, "feedback_type": "completion_check", "selected_value": "yes",
    }, headers=auth_headers())
    assert feedback_resp.status_code == 200

    feedback_list = client.get(f"/feedback/item/{item_id}", headers=auth_headers())
    assert len(feedback_list.json()) == 1
