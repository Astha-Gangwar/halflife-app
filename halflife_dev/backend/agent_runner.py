"""Thin wrapper around the ADK Runner for single-turn agent invocations from
FastAPI routes. Kept separate from the route/agent modules so the runner
plumbing (session service, event iteration) isn't duplicated per caller.
"""
from dataclasses import dataclass
from typing import Optional

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from halflife_agent.agent import root_agent
from halflife_agent.instructions import OUT_OF_SCOPE_REFUSAL

APP_NAME = "halflife"

# A single in-memory session service for the process. Fine for MVP/dev;
# a production deployment would swap this for a persistent SessionService.
_session_service = InMemorySessionService()
_runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=_session_service)


@dataclass
class AgentTurnResult:
    message: str
    # Whether create_item actually succeeded during this turn — derived from
    # the agent's own tool-call events, not guessed from the chat text.
    # Callers (the /capture routes) need this as a real signal so the
    # frontend knows whether to show "confirm this" controls or treat the
    # item as already saved; the chat message alone is not a reliable way
    # to tell (see the confirm-flow bug this was added to help fix).
    item_created: bool
    item_id: Optional[str] = None
    # True when the agent's final response is its fixed out-of-scope
    # refusal, never anything the model paraphrased -- lets callers tell
    # "there's nothing to confirm, this was a flat refusal" apart from a
    # genuine pending classification, which need different UI treatment.
    is_refusal: bool = False


async def run_agent_turn(user_id: str, content: str) -> AgentTurnResult:
    """Send one user message to the agent and report its final text response
    plus whether it actually saved anything.

    Raises whatever the underlying ADK/model call raises (e.g. missing
    credentials, network failure) — the caller is responsible for mapping
    that to a safe user-facing error (Batch 5 VAL-010: a dependency failure
    must not be reported as success).
    """
    session = await _session_service.create_session(app_name=APP_NAME, user_id=user_id)
    message = types.Content(role="user", parts=[types.Part(text=content)])

    final_text = ""
    item_created = False
    item_id: Optional[str] = None

    async for event in _runner.run_async(user_id=user_id, session_id=session.id, new_message=message):
        if event.content and event.content.parts:
            for part in event.content.parts:
                function_response = getattr(part, "function_response", None)
                if function_response and function_response.name == "create_item":
                    envelope = function_response.response or {}
                    if envelope.get("status") == "success":
                        item_created = True
                        item_id = (envelope.get("result") or {}).get("item_id")
            if event.is_final_response() and event.content.parts:
                final_text = "".join(part.text or "" for part in event.content.parts)

    return AgentTurnResult(
        message=final_text, item_created=item_created, item_id=item_id,
        is_refusal=final_text.strip() == OUT_OF_SCOPE_REFUSAL,
    )
