"""Integration tests for the dev-login -> bearer-token -> protected-route
chain, spanning the auth route and the JWT verification dependency together
(neither is meaningfully testable in isolation)."""
import time
import jwt
import pytest
from tests.conftest import auth_headers


def test_dev_login_issues_a_usable_token_for_the_demo_account(api_client):
    resp = api_client.post("/auth/dev-login", json={"user_id": "demo"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = api_client.get("/items/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_dev_login_rejects_any_user_id_other_than_the_demo_account(api_client):
    resp = api_client.post("/auth/dev-login", json={"user_id": "someone-elses-account"})
    assert resp.status_code == 403


def test_missing_authorization_header_is_rejected(api_client):
    resp = api_client.get("/items/")
    assert resp.status_code == 401


def test_malformed_bearer_token_is_rejected(api_client):
    resp = api_client.get("/items/", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_expired_token_is_rejected(api_client):
    from backend.security.authentication import JWT_SECRET, JWT_ALGORITHM
    from datetime import timedelta
    from backend.utils.clock import utcnow

    expired_token = jwt.encode(
        {"sub": "user-1", "exp": utcnow() - timedelta(hours=1)},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )
    resp = api_client.get("/items/", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


def test_token_identity_is_scoped_correctly(api_client):
    api_client.post("/items/", json={
        "user_id": "user-1", "original_content": "private note", "approved_title": "Private",
        "intent_type": "general_note", "approved_analysis_id": "an-1",
    }, headers=auth_headers("user-1"))

    resp = api_client.get("/items/", headers=auth_headers("user-2"))
    assert resp.status_code == 200
    assert resp.json() == []
