import ipaddress
import socket
from typing import Dict, Any
from urllib.parse import urlparse

import requests
from google.adk.tools.tool_context import ToolContext

from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.utils.clock import utcnow

ALLOWED_SCHEMES = {"http", "https"}
MAX_CONTENT_BYTES = 2 * 1024 * 1024  # 2 MB
REQUEST_TIMEOUT_SECONDS = 5
MAX_REDIRECTS = 3


def _is_private_target(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return True  # can't resolve -> treat as unsafe rather than fail open
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return True
    return False


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"UNSUPPORTED_SOURCE: scheme '{parsed.scheme}' is not permitted")
    if not parsed.hostname:
        raise ValueError("INVALID_URL: no hostname in URL")
    if _is_private_target(parsed.hostname):
        raise ValueError("ACCESS_DENIED: target resolves to a private or reserved network")


@as_tool_envelope("retrieve_link_content")
def retrieve_link_content(tool_context: ToolContext, url: str) -> Dict[str, Any]:
    """Retrieve permitted link content for analysis.

    Applies a protocol allow-list, private-network block, redirect
    revalidation, size cap, and timeout — no unrestricted fetching.
    """
    current_url = url
    _validate_url(current_url)

    for _ in range(MAX_REDIRECTS + 1):
        try:
            response = requests.get(
                current_url, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=False,
                stream=True, headers={"User-Agent": "HalfLifeAgent/1.0"},
            )
        except requests.RequestException as e:
            raise ValueError(f"TEMPORARY_UNAVAILABLE: {e}")

        if response.is_redirect or response.status_code in (301, 302, 303, 307, 308):
            next_url = response.headers.get("Location")
            if not next_url:
                raise ValueError("ACCESS_DENIED: redirect with no Location header")
            current_url = next_url
            _validate_url(current_url)
            continue

        if response.status_code != 200:
            raise ValueError(f"ACCESS_DENIED: source returned status {response.status_code}")

        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_CONTENT_BYTES:
            raise ValueError("CONTENT_TOO_LARGE: response exceeds the configured size limit")

        body = b""
        for chunk in response.iter_content(chunk_size=8192):
            body += chunk
            if len(body) > MAX_CONTENT_BYTES:
                raise ValueError("CONTENT_TOO_LARGE: response exceeds the configured size limit")

        return success_envelope("retrieve_link_content", {
            "final_url": current_url,
            "content_type": response.headers.get("Content-Type"),
            "content_text": body.decode(errors="replace")[:20000],
            "retrieved_at": utcnow().isoformat(),
        })

    raise ValueError("ACCESS_DENIED: too many redirects")
