import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env into the process environment as early as possible -- every
# module below (Firestore client, Firebase Admin, the ADK agent's Gemini
# client) reads config straight from os.environ at import/call time via
# os.environ.get(...), with no fallback to reading .env itself. Without
# this, a fresh terminal that hasn't manually exported these vars gets
# confusing failures (e.g. the agent silently missing GOOGLE_API_KEY).
# Cloud Run sets real environment variables directly, so there's no .env
# file to find there and this is a no-op in that environment.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="HalfLife API",
    description="API for the HalfLife personal memory application",
    version="0.1.0"
)

# Configure CORS for local development frontend. The dev server's port can
# vary (e.g. when 3000 is already taken), so allow any localhost origin
# rather than a fixed port list — still scoped to localhost only.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.routes import (
    items, capture, revisit, analyses, attachments, relationships,
    collections, preferences, outcomes, feedback, history, insights, auth,
)

@app.get("/health")
async def health_check():
    """Liveness and readiness check."""
    return {"status": "ok", "service": "halflife-api"}

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(capture.router)
app.include_router(revisit.router)
app.include_router(analyses.router)
app.include_router(attachments.router)
app.include_router(relationships.router)
app.include_router(collections.router)
app.include_router(preferences.router)
app.include_router(outcomes.router)
app.include_router(feedback.router)
app.include_router(history.router)
app.include_router(insights.router)

# Single-container mode: serve the built React frontend from this same
# FastAPI app, so one Cloud Run service handles both the API and the UI —
# no separate Firebase Hosting deployment, no CORS between them (same
# origin). FRONTEND_DIST_PATH points at the frontend's `npm run build`
# output (see the Dockerfile's frontend build stage, which copies it
# there). This is entirely optional and must not break local API-only
# development or the test suite, neither of which build the frontend —
# so everything below is skipped unless that directory actually exists.
#
# Registered last, deliberately: FastAPI matches routes in registration
# order, and the catch-all route below would otherwise swallow every
# request meant for the API routers above it.
FRONTEND_DIST_PATH = Path(os.environ.get("FRONTEND_DIST_PATH", "frontend_dist"))

if FRONTEND_DIST_PATH.is_dir():
    assets_dir = FRONTEND_DIST_PATH / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    _index_html = FRONTEND_DIST_PATH / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """Catch-all for React Router's client-side routes (e.g. /library,
        /revisit) — the browser asks the server for that path directly on a
        hard refresh or a shared link, and the server has no such route of
        its own, so it hands back index.html and lets the already-loaded
        React app's router take over from there. Any real static file
        under FRONTEND_DIST_PATH (e.g. /favicon.ico) is served directly
        instead, if present."""
        requested = FRONTEND_DIST_PATH / full_path
        if full_path and requested.is_file():
            return FileResponse(requested)
        return FileResponse(_index_html)

