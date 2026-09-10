"""The fixed demo account (DEMO_USER_ID, see authentication.py) exists so a
first-time visitor sees a populated app instead of an empty one — but it's
a shared showcase, not a real account, so nothing should ever be able to
write to it. Otherwise one visitor's junk data is what the next visitor
sees.
"""
from tests.conftest import auth_headers
from backend.security.authentication import DEMO_USER_ID


def test_demo_account_can_read(api_client):
    resp = api_client.get("/items/", headers=auth_headers(DEMO_USER_ID))
    assert resp.status_code == 200


def test_demo_account_cannot_create_items(api_client):
    resp = api_client.post("/items/", json={
        "user_id": DEMO_USER_ID, "original_content": "trying to pollute the demo",
        "approved_title": "Nope", "intent_type": "general_note", "approved_analysis_id": "an-1",
    }, headers=auth_headers(DEMO_USER_ID))

    assert resp.status_code == 403
    assert "read-only demo" in resp.json()["detail"].lower()


def test_demo_account_cannot_capture(api_client):
    resp = api_client.post("/capture/", json={
        "content": "buy milk tomorrow", "idempotency_key": "demo-key-1",
    }, headers=auth_headers(DEMO_USER_ID))

    assert resp.status_code == 403


def test_demo_account_cannot_create_collections(api_client):
    resp = api_client.post("/collections/", json={"name": "My List"}, headers=auth_headers(DEMO_USER_ID))
    assert resp.status_code == 403


def test_ordinary_user_is_unaffected(api_client):
    """Sanity check: the guard is scoped to exactly DEMO_USER_ID, not a
    broader change to how writes work for everyone."""
    resp = api_client.post("/items/", json={
        "user_id": "user-1", "original_content": "a real note",
        "approved_title": "Real", "intent_type": "general_note", "approved_analysis_id": "an-1",
    }, headers=auth_headers("user-1"))

    assert resp.status_code == 200
