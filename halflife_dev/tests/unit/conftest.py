import pytest
from mockfirestore import MockFirestore

from backend.db import firestore_connection


@pytest.fixture()
def db_session():
    """A fresh in-memory fake Firestore client per test (see the root
    tests/conftest.py's `_fresh_mock_firestore` for the full explanation —
    this is an identical copy, kept for historical reasons)."""
    firestore_connection.reset_firestore_client_cache()
    mock_db = MockFirestore()
    firestore_connection._client = mock_db
    try:
        yield mock_db
    finally:
        firestore_connection.reset_firestore_client_cache()
