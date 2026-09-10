# HalfLife

A personal memory engine: capture anything in plain language — a task, a
recipe, an idea, a note — and a Gemini-powered agent classifies it and
decides when it should resurface, instead of it being saved once and
forgotten.

## How it works

- **Capture**: type or paste anything into the capture box. A [Google ADK](https://google.github.io/adk-docs/) agent (Gemini 2.5 Flash via Vertex AI) classifies it into one of six content types (task, recipe, idea, learning content, activity log, general note), extracts structured fields, and asks a clarifying question only when the content is genuinely ambiguous — never invents or assumes missing data.
- **Resurface**: a deterministic, code-based lifecycle policy (not another model call) decides when each item is next eligible for review, with a plain-language reason attached to every decision.
- **Organize**: items sharing a category, type, or tag are automatically suggested as related; manual collections group items by topic; Insights surfaces saving/completion behavior over time.

## Stack

- **Frontend**: React 18 + TypeScript (Vite), served as a static build.
- **Backend**: FastAPI (Python), serving both the REST API and the built frontend from one process.
- **Agent**: Google ADK orchestrating Gemini 2.5 Flash via Vertex AI.
- **Database**: Cloud Firestore, scoped per user.
- **Auth**: Firebase Authentication (email/password), plus a fixed read-only demo account for instant, no-signup access.
- **Deployment**: a single container on Cloud Run — one image, one URL.

## Project layout

```
halflife_dev/
  backend/          FastAPI app, routes, services, repositories
  halflife_agent/    ADK agent definition, tools, instructions
  frontend/          React + TypeScript app
  tests/             pytest suite (unit, integration, contract, agent evaluation, e2e)
  Dockerfile          builds the frontend, then bundles it into the backend image
```

## Local setup

**Backend**
```bash
cd halflife_dev
pip install -r requirements.txt
cp .env.example .env   # fill in your own GCP project id and region
uvicorn backend.main:app --reload
```

**Frontend**
```bash
cd halflife_dev/frontend
npm install
cp .env.example .env   # fill in your own Firebase Web app config
npm run dev
```

Both `.env` files are gitignored — nothing in this repo carries real project
IDs or API keys. See each `.env.example` for what's required and why (a
Firebase Web API key is not a secret; your GCP project ID and Vertex AI
region are yours to supply).

**Tests**
```bash
cd halflife_dev
python -m pytest tests/ -q
```

## Deployment

Builds as a single container (see `Dockerfile`) that serves the API and the
built frontend from one FastAPI process, deployed to Cloud Run.
