<a name="readme-top"></a>

<div align="center">
  <img src="assets/favicon.png" alt="Logo" width="100">
  <h1 align="center">DataScope </h1>
</div>

![Python](https://img.shields.io/badge/Python-3.13-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=FastAPI&labelColor=555&logoColor=white) ![LiteLLM](https://img.shields.io/badge/LiteLLM-Multi_Provider-orange) ![PostgresSql](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=Redis&logoColor=white) ![CloudfareR2](https://img.shields.io/static/v1?label=%20&message=Cloudflare%20R2&color=222&logo=Cloudflare) ![TypeScript](https://shields.io/badge/TypeScript-3178C6?logo=TypeScript&logoColor=FFF&style=flat-square) ![NextJs](https://img.shields.io/badge/Next.js-000000?logo=next.js&logoColor=white) 

DataScope is a workspace-based exploratory data analysis app for CSV datasets.
It helps users upload data, inspect schema and quality, run deterministic EDA
tools, generate charts, and ask guided questions about the dataset without
turning the LLM into the source of truth.

The core idea is simple: compute statistics and visualizations with reliable
tooling, then use an agent layer to plan analysis steps and explain the
structured results in plain language.

## **What It Does**

- Organizes analysis around user workspaces and dataset versions.
- Accepts CSV uploads with validation, profiling, and durable storage.
- Runs deterministic EDA tools for overview metrics, column summaries,
  relationships, plotting, and data-quality checks.
- Persists analysis runs, tool executions, generated artifacts, and
  conversation history so work can be resumed.
- Streams live job status to the frontend while keeping Postgres as the
  recovery source.
- Uses LLM providers for planning and interpretation, while keeping raw dataset
  access bounded and tool-driven.

## System Components

```text
src/frontend/       Next.js app for login, workspaces, upload, analysis, charts
src/backend/        FastAPI API, Celery workers, EDA tools, agent orchestration
assets/             Architecture and design images
docs/               Product, API, schema, system, frontend, and agent designs
docker-compose.yml  Local Postgres, Redis, and backend runtime
```

At a high level, the system is split into:

| Component | Role |
| --- | --- |
| Frontend | Next.js UI for workspaces, dataset review, chat, tool selection, and results. |
| API | FastAPI service for auth, uploads, analysis requests, history, and WebSockets. |
| Workers | Celery processes for heavier EDA jobs, plots, retries, and background tasks. |
| Database | Postgres stores users, workspaces, datasets, versions, runs, messages, and artifacts. |
| Queue/cache | Redis backs Celery and stores short-lived reusable analysis outputs. |
| Storage | Cloudflare R2 stores uploaded CSV files and generated plot artifacts. |
| Agent layer | Plans valid tool usage and explains computed results using LLM providers. |

The backend has a more detailed README at
[`src/backend/README.md`](src/backend/README.md), including full API routes,
environment variables, worker commands, and backend-specific rules.

## Local Setup

Prerequisites: Docker Desktop, uv, Node.js.

### 1. Environment variables
- Create `src/backend/.env` (see `.env.example`).
- For local runs use:
  - `DATABASE_URL=postgresql+psycopg://datascope:datascope@localhost:5432/datascope`
  - `REDIS_URL=redis://localhost:6379/0`
- Add the R2, Groq, Gemini and Google OAuth values.
- No spaces around `=` and no quotes around values.

### 2. Start Postgres and Redis
Run from the repository root:
```cmd
docker compose up -d postgres redis
```
- This pulls the images on first run, creates the containers and keeps them running in the background.
- Always name the services. A bare `docker compose up` also starts the compose `backend` service, which clashes with port 8000.

Check they are running (postgres should show healthy):
```cmd
docker compose ps
```

View logs when needed:
```cmd
docker compose logs -f postgres redis
```

### 3. Backend API
```cmd
cd src/backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```
- `alembic upgrade head` creates the database tables. Run it on first setup and after pulling new migrations.
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 4. Celery worker
In a new terminal:
```cmd
cd src/backend
uv run celery -A app.workers.celery_app:celery_app worker --loglevel=info --pool=solo
```

### 5. Frontend
In a new terminal:
```cmd
cd src/frontend
npm install
npm run dev
```
- App: http://localhost:3000

### Stop and reset
Stop the containers and keep the data:
```cmd
docker compose stop postgres redis
```
Remove the containers and keep the data volumes:
```cmd
docker compose down
```
Remove the containers and delete all database data:
```cmd
docker compose down -v
```

----

### Tests

```cmd
cd C:\DataScope\src\backend
uv run pytest
```

The tests cover workspace routes, dataset upload/validation, storage behavior,
analysis routes/tasks, deterministic EDA tools, conversations, and agent
orchestration.

## Current Scope

The current implementation is focused on CSV-first EDA:

- Google OAuth based authentication.
- Workspace and dataset lifecycle APIs.
- Immutable dataset versions for uploaded files.
- Deterministic analysis tools before LLM explanation.
- Live progress updates over WebSockets.
- Tests for routes, services, tools, workers, and orchestration behavior.

Future work can expand this into richer dataset connectors, scheduled analyses,
team collaboration, stronger artifact management, and deeper evaluation suites
for agent behavior.

## Deployment Plans

A practical production deployment can keep the app split by responsibility:

| Layer | Plausible option |
| --- | --- |
| Frontend | Vercel, Netlify, or a containerized Next.js host. |
| API | Containerized FastAPI service on Render, Fly.io, Railway, AWS ECS, GCP Cloud Run, or Kubernetes. |
| Workers | Separate Celery worker process/container scaled independently from the API. |
| Database | Managed Postgres instance via Supabase with automated backups and migration jobs. |
| Redis | Managed Redis for Celery broker, progress events, and hot cache entries. |
| Object storage | Cloudflare R2 bucket for CSV uploads and generated chart files. |
| Secrets | Platform-managed environment variables for OAuth, session, LLM, database, Redis, and R2 credentials. |




## Notes

Detailed Design docs live in `docs/`, while implementation lives under `src/`.The root README is meant to explain the whole platform and deployment shape; service-level
details should stay in the frontend and backend READMEs.
