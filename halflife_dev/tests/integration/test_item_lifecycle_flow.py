"""Integration tests spanning items + collections + preferences + feedback
together — each on its own is unit-tested already; this file checks they
compose correctly through the real HTTP layer, matching how the frontend
actually calls them."""
from tests.conftest import auth_headers


def _create_item(api_client, **overrides):
    payload = {
        "user_id": "user-1", "original_content": "Learn Rust ownership model",
        "approved_title": "Rust Ownership", "intent_type": "learning_content",
        "approved_analysis_id": "an-1",
    }
    payload.update(overrides)
    resp = api_client.post("/items/", json=payload, headers=auth_headers())
    assert resp.status_code == 200
    return resp.json()


def test_create_search_update_archive_flow(api_client):
    item = _create_item(api_client)

    search_resp = api_client.get("/items/?query=Rust", headers=auth_headers())
    assert any(i["item_id"] == item["item_id"] for i in search_resp.json())

    patch_resp = api_client.patch(f"/items/{item['item_id']}", json={
        "approved_summary": "Ownership, borrowing, and lifetimes.",
        "expected_version": item["version"],
    }, headers=auth_headers())
    assert patch_resp.status_code == 200
    assert patch_resp.json()["approved_summary"] == "Ownership, borrowing, and lifetimes."

    archive_resp = api_client.post(f"/items/{item['item_id']}/status?action=archive", headers=auth_headers())
    assert archive_resp.json()["status"] == "archived"

    restore_resp = api_client.post(f"/items/{item['item_id']}/status?action=restore", headers=auth_headers())
    assert restore_resp.json()["status"] == "active"


def test_item_collection_membership_flow(api_client):
    item = _create_item(api_client)

    create_collection = api_client.post("/collections/", json={"name": "Rust Learning"}, headers=auth_headers())
    collection_id = create_collection.json()["collection_id"]

    add_resp = api_client.post(f"/collections/{collection_id}/items/{item['item_id']}", headers=auth_headers())
    assert add_resp.status_code == 200

    items_resp = api_client.get(f"/collections/{collection_id}/items", headers=auth_headers())
    assert items_resp.json() == [item["item_id"]]

    remove_resp = api_client.delete(f"/collections/{collection_id}/items/{item['item_id']}", headers=auth_headers())
    assert remove_resp.status_code == 200
    assert api_client.get(f"/collections/{collection_id}/items", headers=auth_headers()).json() == []


def test_feedback_flow(api_client):
    item = _create_item(api_client)

    resp = api_client.post("/feedback/", json={
        "item_id": item["item_id"], "feedback_type": "usefulness", "selected_value": "yes",
    }, headers=auth_headers())
    assert resp.status_code == 200

    list_resp = api_client.get(f"/feedback/item/{item['item_id']}", headers=auth_headers())
    assert len(list_resp.json()) == 1


def test_preferences_round_trip(api_client):
    initial = api_client.get("/preferences/", headers=auth_headers())
    assert initial.status_code == 200
    assert initial.json()["preferred_recipe_days"] == []

    updated = api_client.patch("/preferences/", json={
        "preferred_recipe_days": ["friday", "saturday"],
        "timezone": "America/New_York",
    }, headers=auth_headers())
    assert updated.json()["preferred_recipe_days"] == ["friday", "saturday"]
    assert updated.json()["timezone"] == "America/New_York"

    refetched = api_client.get("/preferences/", headers=auth_headers())
    assert refetched.json()["preferred_recipe_days"] == ["friday", "saturday"]


def test_outcome_requires_lifecycle_assignment(api_client):
    item = _create_item(api_client)

    # Items created directly via the REST API (rather than through the
    # agent's create_item tool) don't get a lifecycle assignment — this
    # should fail cleanly (409), not crash.
    resp = api_client.post(f"/outcomes/{item['item_id']}", json={"outcome": "tried"}, headers=auth_headers())
    assert resp.status_code == 409


def test_recording_an_outcome_via_the_rest_route_updates_the_items_display_state(api_client):
    """Regression test: the frontend calls POST /outcomes/{id} directly
    (not the agent tool) when a user clicks Tried it/Completed/etc. That
    route only ever updated the separate lifecycle_assignments record,
    never the item's own current_lifecycle_state -- the field the item
    detail page actually displays -- so the click looked like it did
    nothing."""
    from types import SimpleNamespace
    from unittest.mock import patch
    from contextlib import contextmanager
    from backend.tools import item_tools
    from backend.db import firestore_connection

    @contextmanager
    def _session_from(db):
        yield db

    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(firestore_connection.get_firestore_client())):
        created = item_tools.create_item(
            SimpleNamespace(user_id="user-1"),
            original_content="Submit tax documents by Friday",
            intent="task",
            title="Submit tax documents",
            intent_attributes={"action_text": "Submit tax documents", "due_at": "2026-09-08T00:00:00", "priority": "high"},
        )
    item_id = created["result"]["item_id"]

    resp = api_client.post(f"/outcomes/{item_id}", json={"outcome": "completed"}, headers=auth_headers())
    assert resp.status_code == 200

    fetched = api_client.get(f"/items/{item_id}", headers=auth_headers())
    assert fetched.json()["current_lifecycle_state"] == "completed"
