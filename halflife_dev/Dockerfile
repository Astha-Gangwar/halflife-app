# Single-container image: builds the React frontend, then bundles it
# alongside the FastAPI backend so one Cloud Run service serves both —
# see backend/main.py's FRONTEND_DIST_PATH mount for how the backend picks
# this up. Cloud Run injects the port to listen on via the `PORT` env var
# (defaults to 8080 if unset, e.g. when running the image locally with
# `docker run`).

# --- Stage 1: build the frontend ---
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: the actual backend image ---
FROM python:3.12-slim
WORKDIR /app

# Install dependencies first so this layer is cached across code-only changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code. The Gemini/ADK agent package (halflife_agent) is
# imported by the backend at runtime and must ship in the same image.
COPY backend ./backend
COPY halflife_agent ./halflife_agent

# The built frontend from stage 1 — backend/main.py serves this directly
# when FRONTEND_DIST_PATH (defaulting to "frontend_dist", relative to this
# WORKDIR) exists, which it now does inside this image.
COPY --from=frontend-build /app/frontend/dist ./frontend_dist

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

# Shell form so ${PORT} is expanded by the shell at container start —
# Cloud Run always sets PORT, but the default keeps `docker run` usable too.
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
