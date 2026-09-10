from contextlib import contextmanager
from backend.db.firestore_connection import get_firestore_client

@contextmanager
def tool_db_session():
    """Yields the shared Firestore client for use inside a tool call.

    Kept as a context manager (rather than a plain function call) so every
    tool file's existing `with tool_db_session() as db:` shape didn't need
    to change when this project moved off SQLite — only the object it
    yields changed, from a SQLAlchemy Session to a Firestore client.
    Firestore's client is a lightweight, reusable singleton with no
    per-call connection to open or close, unlike a SQL session.
    """
    yield get_firestore_client()
