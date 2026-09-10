"""Regression tests for a real bug found via manual UI testing: when
run_agent_turn raised (e.g. Google's quota-exhausted error), the route did
`f"Agent temporarily unavailable: {e}"` — str(e) on that exception includes
the ENTIRE raw provider error payload (doc links, quota metrics, JSON blobs),
which then reached the end user verbatim in the API response and the UI.
No exception's raw text should ever reach the client; _agent_call_failed in
capture.py now classifies the failure and returns a short, safe message.
"""
from unittest.mock import patch, AsyncMock
from tests.conftest import auth_headers

_RAW_QUOTA_ERROR = (
    "429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded "
    "your current quota, please check your plan and billing details. For more "
    "information on this error, head to: https://ai.google.dev/gemini-api/docs/"
    "rate-limits.', 'status': 'RESOURCE_EXHAUSTED', 'details': [...]}}"
)


def test_quota_exhausted_error_is_not_leaked_to_the_client(api_client):
    with patch("backend.api.routes.capture.run_agent_turn", new_callable=AsyncMock) as mock_agent:
        mock_agent.side_effect = Exception(_RAW_QUOTA_ERROR)
        resp = api_client.post("/capture/", json={
            "content": "buy milk tomorrow",
            "idempotency_key": "err-key-1",
        }, headers=auth_headers())

    assert resp.status_code == 429
    detail = resp.json()["detail"]
    assert "RESOURCE_EXHAUSTED" not in detail
    assert "ai.google.dev" not in detail
    assert "usage limit" in detail.lower()


def test_generic_agent_failure_is_not_leaked_to_the_client(api_client):
    with patch("backend.api.routes.capture.run_agent_turn", new_callable=AsyncMock) as mock_agent:
        mock_agent.side_effect = Exception("some internal stack trace or credential path detail")
        resp = api_client.post("/capture/", json={
            "content": "buy milk tomorrow",
            "idempotency_key": "err-key-2",
        }, headers=auth_headers())

    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert "internal stack trace" not in detail
    assert "temporarily unavailable" in detail.lower()


def test_confirm_route_also_hides_raw_errors(api_client):
    with patch("backend.api.routes.capture.run_agent_turn", new_callable=AsyncMock) as mock_agent:
        mock_agent.side_effect = Exception(_RAW_QUOTA_ERROR)
        resp = api_client.post("/capture/confirm", json={
            "original_content": "buy milk tomorrow",
        }, headers=auth_headers())

    assert resp.status_code == 429
    assert "RESOURCE_EXHAUSTED" not in resp.json()["detail"]
