"""Detects content that looks like it contains a password, API key, or other
credential, so capture.py can keep it out of the external Gemini call while
still saving it for the user (Batch 3 §18: "Secrets and tokens must never be
stored in item, analysis, feedback, or event metadata" — here it's about not
*transmitting* a credential to a third-party model in the first place, since
the model never gets a chance to persist it if it's never sent).

This is a conservative heuristic, not a secret scanner: it is tuned to catch
common phrasing ("my password is...", "api_key=...") even at the cost of
occasional false positives, because the cost of skipping agent analysis for
a false positive (the user gets a plain save instead of auto-classification)
is far lower than the cost of a false negative (a real credential reaching
an external LLM).
"""
import re

_CREDENTIAL_KEYWORDS = r"(?:password|passwd|pwd|api[_\s-]?key|secret[_\s-]?key|access[_\s-]?key|auth[_\s-]?token|api[_\s-]?token|private[_\s-]?key)"

_PATTERNS = [
    # "password is X", "my password: X", "pwd = X"
    re.compile(rf"\b{_CREDENTIAL_KEYWORDS}\b\s*(?:is|are|[:=])\s*\S+", re.IGNORECASE),
    # key=value assignment style: PASSWORD=hunter2, api_key: "sk-..."
    re.compile(rf"\b{_CREDENTIAL_KEYWORDS}\b\s*[:=]", re.IGNORECASE),
    # common cloud secret key prefixes
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),  # OpenAI/Anthropic-style secret key
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),  # Google API key
]


def looks_like_credential(text: str) -> bool:
    """Return True if `text` appears to contain a password or other secret."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _PATTERNS)
