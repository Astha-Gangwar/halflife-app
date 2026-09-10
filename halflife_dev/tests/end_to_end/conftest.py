import os
import pytest
from mockfirestore import MockFirestore

from backend.db import firestore_connection


@pytest.fixture()
def e2e_env():
    """Like the shared `api_client` fixture, but also exposes the raw fake
    Firestore client, so a test can simulate an agent tool call (which
    builds its own repository via `tool_db_session`) alongside real HTTP
    requests against the same data — reproducing how capture.py's
    agent-driven path and the direct REST routes actually share one
    Firestore instance in production.
    """
    os.environ["AUTH_MODE"] = "jwt"

    firestore_connection.reset_firestore_client_cache()
    mock_db = MockFirestore()
    firestore_connection._client = mock_db

    from backend.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    try:
        yield client, mock_db
    finally:
        firestore_connection.reset_firestore_client_cache()
