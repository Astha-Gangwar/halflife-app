"""Firestore client access.

The client talks to Google Cloud Firestore using Application Default
Credentials (ADC) — this works automatically on Cloud Run, and locally via
either `gcloud auth application-default login` or a service-account key
referenced by the `GOOGLE_APPLICATION_CREDENTIALS` env var.

The client is created lazily and cached as a module-level singleton so that
importing this module (e.g. transitively, via the repository factory) never
requires GCP credentials to be present. It is only actually constructed the
first time `get_firestore_client()` is called, which happens only when a
request is served with `REPO_BACKEND=firestore`. This keeps `pytest` and
local sqlite-mode development working with zero GCP setup.
"""
import os
from typing import Optional

_client: Optional["object"] = None


def get_firestore_client():
    """Return a process-wide cached `google.cloud.firestore.Client`.

    Import of the `google.cloud.firestore` package itself is deferred to
    call time (rather than module import time) so that environments without
    the dependency installed, or without GCP credentials configured, are
    unaffected as long as this function is never invoked.
    """
    global _client
    if _client is None:
        from google.cloud import firestore  # deferred import

        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        database_id = os.environ.get("FIRESTORE_DATABASE_ID", "(default)")
        if project_id:
            _client = firestore.Client(project=project_id, database=database_id)
        else:
            _client = firestore.Client(database=database_id)
    return _client


def reset_firestore_client_cache() -> None:
    """Test helper: drop the cached client so a fresh one is built next call."""
    global _client
    _client = None
