from datetime import datetime, timezone
from typing import Any, Dict


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (no tzinfo).

    Replaces the deprecated datetime.utcnow(). Deliberately still naive,
    not timezone-aware: every domain schema and Firestore repository in
    this project was written against naive datetimes (comparisons like
    `due_at < now` throughout backend/services/lifecycle_policies.py
    assume both sides are naive), so switching to an aware datetime here
    would raise "can't compare offset-naive and offset-aware datetimes"
    the moment it's compared against one of those. This is the one place
    that knows the conversion; everything else just calls utcnow().
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_firestore_datetimes(data: Dict[str, Any]) -> Dict[str, Any]:
    """Strip tzinfo from every top-level datetime value in a Firestore
    document dict, immediately after `.to_dict()`.

    This was a real bug, not a theoretical one: the Firestore client
    returns timezone-aware (UTC) datetimes on read, even for values that
    were stored as naive via utcnow() — so `assignment.next_review_date >
    now` (comparing a value just read back against a freshly computed
    naive utcnow()) raised "can't compare offset-naive and offset-aware
    datetimes" the moment this ran against real Firestore. The project's
    test suite never caught this because its fake Firestore client
    (mock-firestore) doesn't replicate this specific real-GCP behavior —
    it just stores and returns whatever was passed in, naive or not.

    Every Firestore repository must call this on the dict returned by
    `.to_dict()` before building a domain object from it — one call site
    per read, rather than hunting down every individual datetime field
    name across 11 files (and every field added in the future).
    """
    return {
        key: (value.replace(tzinfo=None) if isinstance(value, datetime) and value.tzinfo is not None else value)
        for key, value in data.items()
    }
