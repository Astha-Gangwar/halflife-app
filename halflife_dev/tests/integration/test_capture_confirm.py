"""Regression tests for the capture confirm bug found by manual testing:
POST /capture/confirm used to forward only an analysis_id to the agent
(f"Here is my correction for analysis {analysis_id}: {response}"), never the
original content. Since every run_agent_turn call starts a brand-new,
memory-less ADK session, the agent had no way to know what to save, so
confirming a prior capture silently saved nothing. The fix requires the
caller to resend original_content, which the route now forwards verbatim.
"""
from unittest.mock import patch, AsyncMock
from tests.conftest import auth_headers
from backend.agent_runner import AgentTurnResult


def test_confirm_forwards_the_original_content_to_the_agent(api_client):
    with patch("backend.api.routes.capture.run_agent_turn", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = AgentTurnResult(message="Saved.", item_created=True, item_id="item-123")
        resp = api_client.post("/capture/confirm", json={
            "original_content": "try recipe with paneer and dosa batter next week",
            "corrections": {"intent": "recipe"},
        }, headers=auth_headers())

    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    mock_agent.assert_called_once()
    _, sent_text = mock_agent.call_args.args
    assert "paneer and dosa batter" in sent_text
    assert "recipe" in sent_text


def test_confirm_without_corrections_still_asks_the_agent_to_save_as_understood(api_client):
    with patch("backend.api.routes.capture.run_agent_turn", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = AgentTurnResult(message="Saved.", item_created=True, item_id="item-123")
        resp = api_client.post("/capture/confirm", json={
            "original_content": "renew my passport next month",
        }, headers=auth_headers())

    assert resp.status_code == 200
    _, sent_text = mock_agent.call_args.args
    assert "renew my passport next month" in sent_text
    assert "save it as understood" in sent_text


def test_confirm_requires_original_content(api_client):
    resp = api_client.post("/capture/confirm", json={
        "corrections": {"intent": "recipe"},
    }, headers=auth_headers())

    assert resp.status_code == 422
