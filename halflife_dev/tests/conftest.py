import pytest
from mockfirestore import MockFirestore

from backend.db import firestore_connection


def _fresh_mock_firestore():
    """Point backend.db.firestore_connection.get_firestore_client() at a
    fresh in-memory fake for the duration of one test, instead of a real
    GCP connection. get_firestore_client() caches its client at module
    level, so setting that cache directly (rather than trying to inject
    a fixture through FastAPI's Depends()) is what actually makes every
    repository — constructed directly in a test, or built inside a route
    via repositories/factory.py — see the same fake data store."""
    firestore_connection.reset_firestore_client_cache()
    mock_db = MockFirestore()
    firestore_connection._client = mock_db
    return mock_db


@pytest.fixture()
def db_session():
    """A fresh in-memory fake Firestore client per test. Named `db_session`
    for historical reasons (this project used to run tests against a real
    SQLite session) — the name stuck since so many tests already reference
    it, but it now yields a `MockFirestore` instance, not a SQL session."""
    mock_db = _fresh_mock_firestore()
    try:
        yield mock_db
    finally:
        firestore_connection.reset_firestore_client_cache()


@pytest.fixture()
def api_client():
    """A FastAPI TestClient backed by a fresh fake Firestore store, with
    AUTH_MODE forced to jwt. Unlike the old SQLite-era version, there's no
    FastAPI dependency to override — repositories/factory.py calls
    get_firestore_client() directly, so pointing its module-level cache at
    a fake client (done in _fresh_mock_firestore) is what real routes end
    up using too."""
    import os
    os.environ["AUTH_MODE"] = "jwt"
    _fresh_mock_firestore()

    from backend.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    try:
        yield client
    finally:
        firestore_connection.reset_firestore_client_cache()


def auth_headers(user_id: str = "user-1") -> dict:
    """Build a valid Authorization header for `user_id` without going through
    the dev-login HTTP round trip."""
    import jwt
    from datetime import timedelta
    from backend.utils.clock import utcnow
    from backend.security.authentication import JWT_SECRET, JWT_ALGORITHM

    token = jwt.encode(
        {"sub": user_id, "exp": utcnow() + timedelta(hours=1)},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}
