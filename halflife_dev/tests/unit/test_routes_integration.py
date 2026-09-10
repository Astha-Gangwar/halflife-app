import os
import jwt as pyjwt
from datetime import timedelta
from backend.utils.clock import utcnow

os.environ.setdefault("AUTH_MODE", "jwt")


def _auth_headers(user_id="user-1"):
    from backend.security.authentication import JWT_SECRET, JWT_ALGORITHM
    token = pyjwt.encode({"sub": user_id, "exp": utcnow() + timedelta(hours=1)}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


def test_missing_auth_is_rejected(api_client):
    resp = api_client.get("/items/")
    assert resp.status_code == 401


def test_create_and_fetch_item(api_client):
    headers = _auth_headers()
    payload = {
        "user_id": "user-1", "original_content": "Learn Rust",
        "approved_title": "Rust Basics", "intent_type": "learning_content",
        "approved_analysis_id": "an-1",
    }
    resp = api_client.post("/items/", json=payload, headers=headers)
    assert resp.status_code == 200
    item_id = resp.json()["item_id"]

    resp = api_client.get(f"/items/{item_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["approved_title"] == "Rust Basics"


def test_idempotency_replay_and_conflict(api_client):
    headers = {**_auth_headers(), "Idempotency-Key": "key-1"}
    payload = {
        "user_id": "user-1", "original_content": "Learn Go",
        "approved_title": "Go Basics", "intent_type": "learning_content",
        "approved_analysis_id": "an-1",
    }
    resp1 = api_client.post("/items/", json=payload, headers=headers)
    resp2 = api_client.post("/items/", json=payload, headers=headers)
    assert resp1.json()["item_id"] == resp2.json()["item_id"]

    conflicting = dict(payload, original_content="Learn Zig")
    resp3 = api_client.post("/items/", json=conflicting, headers=headers)
    assert resp3.status_code == 409


def test_collection_membership_flow(api_client):
    headers = _auth_headers()
    item = api_client.post("/items/", json={
        "user_id": "user-1", "original_content": "note", "approved_title": "Note",
        "intent_type": "general_note", "approved_analysis_id": "an-1",
    }, headers=headers).json()

    collection = api_client.post("/collections/", json={"name": "Reading List"}, headers=headers).json()
    resp = api_client.post(f"/collections/{collection['collection_id']}/items/{item['item_id']}", headers=headers)
    assert resp.status_code == 200

    items = api_client.get(f"/collections/{collection['collection_id']}/items", headers=headers).json()
    assert items == [item["item_id"]]


def test_cross_user_item_access_is_denied(api_client):
    item = api_client.post("/items/", json={
        "user_id": "user-1", "original_content": "secret", "approved_title": "Secret",
        "intent_type": "general_note", "approved_analysis_id": "an-1",
    }, headers=_auth_headers("user-1")).json()

    resp = api_client.get(f"/items/{item['item_id']}", headers=_auth_headers("user-2"))
    assert resp.status_code == 404
