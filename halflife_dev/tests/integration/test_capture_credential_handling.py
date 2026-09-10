"""Security test case: a user captures content containing what looks like a
password. HalfLife must still save it (it's the user's own data, and a
capture tool that silently drops content is worse than one that stores it),
but must NEVER forward it to the external Gemini agent — see Batch 3 §18
("secrets and tokens must never be stored...") and capture.py's
`_save_without_agent_analysis`.
"""
from unittest.mock import patch, AsyncMock
from tests.conftest import auth_headers
from backend.agent_runner import AgentTurnResult


def test_capturing_a_password_saves_the_item_without_calling_the_agent(api_client):
    with patch("backend.api.routes.capture.run_agent_turn", new_callable=AsyncMock) as mock_agent:
        resp = api_client.post("/capture/", json={
            "content": "my email password is hunter2, don't forget it",
            "idempotency_key": "key-1",
        }, headers=auth_headers())

        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert "item_id" in resp.json()
        mock_agent.assert_not_called()


def test_the_saved_password_item_is_retrievable_and_stored_as_is(api_client):
    with patch("backend.api.routes.capture.run_agent_turn", new_callable=AsyncMock):
        resp = api_client.post("/capture/", json={
            "content": "api_key=sk-thisisaveryveryverylongfakesecretkey1234",
            "idempotency_key": "key-2",
        }, headers=auth_headers())
    item_id = resp.json()["item_id"]

    get_resp = api_client.get(f"/items/{item_id}", headers=auth_headers())
    assert get_resp.status_code == 200
    item = get_resp.json()
    # The original content is preserved exactly — capture never redacts or
    # rejects the user's own data, it only withholds it from the LLM call.
    assert item["original_content"] == "api_key=sk-thisisaveryveryverylongfakesecretkey1234"
    assert item["intent_type"] == "general_note"


def test_ordinary_content_still_goes_to_the_agent(api_client):
    with patch("backend.api.routes.capture.run_agent_turn", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = AgentTurnResult(message="Saved as a recipe.", item_created=True, item_id="item-123")
        resp = api_client.post("/capture/", json={
            "content": "I want to try making sourdough bread this weekend",
            "idempotency_key": "key-3",
        }, headers=auth_headers())

    assert resp.status_code == 200
    mock_agent.assert_called_once()
    assert resp.json()["message"] == "Saved as a recipe."
    assert resp.json()["item_created"] is True
    assert resp.json()["item_id"] == "item-123"
