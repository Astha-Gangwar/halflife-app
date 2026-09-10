"""Regression tests for a real bug found in production, not in this test
suite: real Firestore returns timezone-aware (UTC) datetimes on read, even
for values stored as naive via utcnow() — this project's fake Firestore
client (mock-firestore) doesn't replicate that specific behavior, so it
took a live run against real GCP to surface
"TypeError: can't compare offset-naive and offset-aware datetimes" inside
ResurfacingService.get_revisit_candidates.
"""
from datetime import datetime, timezone
from backend.utils.clock import normalize_firestore_datetimes


def test_strips_tzinfo_from_aware_datetimes():
    aware = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    result = normalize_firestore_datetimes({"next_review_date": aware, "name": "x"})
    assert result["next_review_date"].tzinfo is None
    assert result["next_review_date"] == aware.replace(tzinfo=None)
    assert result["name"] == "x"


def test_leaves_already_naive_datetimes_unchanged():
    naive = datetime(2026, 9, 10, 12, 0, 0)
    result = normalize_firestore_datetimes({"created_at": naive})
    assert result["created_at"] == naive
    assert result["created_at"].tzinfo is None


def test_leaves_non_datetime_values_unchanged():
    data = {"user_id": "user-1", "version": 3, "tags": ["a", "b"], "note": None}
    assert normalize_firestore_datetimes(data) == data


def test_handles_multiple_datetime_fields_independently():
    aware = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    naive = datetime(2026, 9, 1, 8, 0, 0)
    result = normalize_firestore_datetimes({
        "created_at": aware, "updated_at": naive, "archived_at": None,
    })
    assert result["created_at"].tzinfo is None
    assert result["updated_at"].tzinfo is None
    assert result["archived_at"] is None
