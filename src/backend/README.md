# DataScope Backend

FastAPI backend for DataScope, a workspace-based exploratory data analysis app.
The backend owns authentication, workspace state, CSV ingestion, deterministic
EDA execution, LLM-assisted interpretation, persisted analysis history, and live
job updates.

![Backend design](../../assets/BackendDesign.png)

## Architecture

The service is built around a small number of durable records: users,
workspaces, datasets, immutable dataset versions, conversations, analysis runs,
tool executions, and artifacts. Postgres is the source of truth for those
records. Redis is used for Celery queueing and short-lived cached analysis
results. Cloudflare R2 stores uploaded CSVs and generated plot artifacts.

At runtime the flow is:

1. Google OAuth signs in a user and creates an application session.
2. The user creates a workspace and uploads a CSV.
3. The upload is validated, profiled, stored in R2, and recorded as a dataset
   version.
4. The user starts an analysis run through selected deterministic tools or a
   dataset question.
5. FastAPI persists the run first, then either executes it inline for small
   simple requests or queues it to Celery for heavier work.
6. Workers run deterministic EDA tools, cache reusable outputs, generate
   artifacts, and ask the LLM only to plan or explain structured results.
7. The frontend recovers state from REST endpoints and receives live progress
   over WebSockets.

## Main Modules

```text
app/
  api/routes/       Auth, workspace, dataset, analysis, result, chat, health, WS
  core/             Settings, logging, exception handling, session security
  db/models/        SQLAlchemy models for all persisted backend records
  eda_tools/        Deterministic EDA tools: high_level, column, relationships, quality
  agent/            Planner/interpreter orchestration contracts and prompts
  services/         Business logic for auth, storage, datasets, runs, cache, events
  workers/          Celery app and background analysis/retention tasks
alembic/            Database migrations
tests/              Route, service, tool, and orchestration tests
```

## API Surface

All API routes are mounted under `/api/v1`.

| Area | Routes |
| --- | --- |
| Auth | `GET /auth/google/login`, `GET /auth/google/callback`, `GET /auth/me`, `POST /auth/logout` |
| Workspaces | `POST /workspaces`, `GET /workspaces`, `GET /workspaces/{id}`, `PATCH /workspaces/{id}`, `DELETE /workspaces/{id}`, `POST /workspaces/{id}/restore` |
| Datasets | `POST /workspaces/{id}/datasets`, `GET /workspaces/{id}/datasets`, `GET /datasets/{id}/overview`, `DELETE /datasets/{id}` |
| Analysis | `GET /analysis/tools`, `POST /datasets/{id}/analysis-runs`, `GET /analysis-runs/{id}`, `POST /analysis-runs/{id}/retry`, `POST /analysis-runs/{id}/cancel` |
| Results | `GET /datasets/{id}/analysis-runs`, `GET /analysis-runs/{id}/results`, `GET /analysis-runs/{id}/artifacts` |
| Conversation | `POST /datasets/{id}/conversation`, `POST /datasets/{id}/messages`, `GET /datasets/{id}/messages`, `GET /datasets/{id}/question-usage`, `PATCH /conversations/{id}/columns` |
| Realtime | `WS /ws/workspaces/{id}` |
| Operations | `GET /health`, `GET /ready` |

## V1 Backend Rules

- CSV uploads only.
- Upload limit defaults: 25 MB, 200,000 rows, 100 columns.
- Every upload creates a new immutable dataset version.
- Analysis runs are persisted before compute starts.
- Small single-tool runs can execute inline; multi-tool, plot, relationship, or
  larger runs are queued to Celery.
- WebSockets are only for live progress. Postgres remains the recovery source.
- Raw CSV data is not sent to the LLM. The LLM receives compact structured
  summaries, computed metrics, selected samples only when bounded, and tool
  outputs.
- Cache keys are based on dataset version, tool name, normalized arguments, and
  tool version. Redis is the hot cache; Postgres keeps completed runs through
  workspace retention.
- Workspace retention defaults to 30 inactive days plus a 7 day restore window.

## Local Setup

Install dependencies:

```powershell
cd C:\DataScope\src\backend
uv sync
```

Start local Postgres and Redis from the repo root:

```powershell
cd C:\DataScope
docker compose up postgres redis
```

Configure `src/backend/.env`:

```env
APP_ENV=local
DEBUG=true
DOCS_ENABLED=true
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=["http://localhost:3000"]

SESSION_SECRET_KEY=replace-me

GOOGLE_CLIENT_ID=replace-me
GOOGLE_CLIENT_SECRET=replace-me
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

GOOGLE_API_KEY=replace-me
GROQ_API_KEY=replace-me

DATABASE_URL=postgresql+psycopg://datascope:datascope@localhost:5432/datascope
REDIS_URL=redis://localhost:6379/0

R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=replace-me
R2_SECRET_ACCESS_KEY=replace-me
R2_BUCKET_NAME=replace-me
R2_REGION_NAME=auto
```

Run migrations and start the API:

```powershell
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## Workers

Analysis jobs that are not executed inline require a Celery worker:

```powershell
cd C:\DataScope\src\backend
uv run celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```

Redis must be available through `REDIS_URL` for queued runs, progress events,
and hot cache reuse.

## Tests

```powershell
cd C:\DataScope\src\backend
uv run pytest
```

The tests cover workspace routes, dataset upload/validation, storage behavior,
analysis routes/tasks, deterministic EDA tools, conversations, and agent
orchestration.

## Deployment Shape

The intended split is:

```text
Frontend:  Vercel or another Next.js host
Backend:   FastAPI API and Celery worker
Database:  Managed Postgres
Queue:     Redis
Storage:   Cloudflare R2
Auth:      Google OAuth
LLM:       LiteLLM-backed Google/Groq providers
```

Use Docker Compose locally for Postgres and Redis. For production, keep
Postgres and R2 managed, set all secrets through the deployment platform, and
run the API and worker as separate processes or containers.
