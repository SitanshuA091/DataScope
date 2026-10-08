# DataScope

DataScope is a workspace-based exploratory data analysis app for CSV datasets.
It helps users upload data, inspect schema and quality, run deterministic EDA
tools, generate charts, and ask guided questions about the dataset without
turning the LLM into the source of truth.

The core idea is simple: compute statistics and visualizations with reliable
tooling, then use an agent layer to plan analysis steps and explain the
structured results in plain language.

## What It Does

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

## Local Development

Start infrastructure and the backend from the repository root:

```powershell
docker compose up postgres redis backend
```

Start the frontend in a second terminal:

```powershell
cd src/frontend
npm install
npm run dev
```

Useful local URLs:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
API docs: http://localhost:8000/docs
```

For direct backend development without the Docker backend service, use
`uv` inside `src/backend`, configure `.env`, run Alembic migrations, and start
Uvicorn as described in the backend README.

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
| Database | Managed Postgres with automated backups and migration jobs. |
| Redis | Managed Redis for Celery broker, progress events, and hot cache entries. |
| Object storage | Cloudflare R2 bucket for CSV uploads and generated chart files. |
| Secrets | Platform-managed environment variables for OAuth, session, LLM, database, Redis, and R2 credentials. |

Recommended rollout path:

1. Deploy frontend and backend separately, with the frontend calling the backend
   through a stable public API URL.
2. Run database migrations as a release step before new backend containers
   receive traffic.
3. Run API and Celery workers as separate services so analysis jobs do not block
   request handling.
4. Keep Postgres and object storage managed from the start; they are the
   important durable parts of the system.
5. Add CI checks for backend tests, frontend lint/build, and migration sanity
   before enabling automatic deployment.

## Notes

Design docs live in `docs/`, while implementation lives under `src/`. The root
README is meant to explain the whole product and deployment shape; service-level
details should stay in the frontend and backend READMEs.
