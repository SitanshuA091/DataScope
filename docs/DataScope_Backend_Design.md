# DataScope — Backend Design (consolidated)

Merges: earlier backend summary + Agent&Tooldesign, APIDesign, backendV1, prouctdesign, SchemaDesign, SysDesign, and the later chat/frontend contract findings.

## 0. Naming Notes
- Product name used in your docs: DataScope; backend config currently says "DataLens API" (app_name) and the previous summary used DataLens; pick one and align config.py, README, frontend titles
- Suggested file names: DataScope_Backend_Design.md and DataScope_Frontend_Design.md (or docs/backend.md and docs/frontend.md)

## 1. Product Intent and Scope
- Stateful AI data-analysis workspace with an agent interface, not "upload CSV -> chatbot gives EDA"
- Computation stays in deterministic EDA tools; LLM only selects tools, extracts parameters, explains structured output
- LLM must never invent statistics; explanations grounded in supplied results
- V1 demonstrates: persistence, resumability, controlled tools, background work for expensive tasks, cached repeat analysis, history, transparent results
- Not required: collaborative workspaces, scheduled analyses, many file types, enterprise permissions, Kubernetes, Airflow, multiple queues

## 2. Agent Capabilities and Tools
- Upload via upload endpoint; validated; only lightweight overview shown (rows, columns, names/types); no automatic full EDA
- User chooses what to investigate; agent picks tool(s)
- High-Level EDA Tool: dataset-level stats, distributions, missing values, numeric summaries, overview plots
- Column-Specific EDA Tool: describe(), value counts, distribution, cardinality, plots for selected columns
- Relationship/Correlation Tool: correlations, grouped stats, scatter/box plots, heatmap
- Data Quality Tool: missingness, duplicates, constant/high-cardinality columns, outliers, suspicious values
- Chatbot question: original idea "persist a dataframe in DB and feed to LLM" is rejected (see section 10); chat runs through the same controlled tool flow
- Per-conversation question cap (10)
- Ambiguous requests ("find issues") trigger a quality-oriented investigation; missing column -> agent asks or states limitation
- Clarification path: planner can return requires_clarification with a clarification_question instead of tools

## 3. Product Requirements (scenarios)
- Account/workspace: user sees earlier workspaces; each upload becomes a workspace with schema, conversations, runs, charts, findings; rename/reopen/delete
- Upload readiness: immediate confirmation; quick overview for small files, processing state for larger; actionable errors for encoding, malformed rows, unsupported format, limits
- Resumable sessions: close tab and reopen; restore completed results, chat context, selected columns, last status of in-progress request; visible states (queued/running/completed/failed/cancelled); retry failed analysis without recreating workspace
- Background analysis: correlation heatmap over many columns, detailed quality report, many high-cardinality distributions, baseline model; run independent of the browser, report progress, save results; transient failure -> retry; permanent -> failure plus retry option
- Fast vs queued: schema/types and single numeric describe() feel instant; dataset-wide scans, large plots, model training use job status UI
- Cached results: repeat high-level EDA reuses result; revisiting a column reuses stats and plots; changed dataset or parameters = new result; caching controls compute and LLM cost
- History/reproducibility: record request, tools, parameters, structured output, plots, explanation, timestamp, status; answer "how did the app reach this conclusion?"; reopen prior results
- Conversation/context: understands "compare that with salary" and "missing values for the previous columns"; stores compact session context; retrieves only relevant prior analysis context
- Dataset versions: corrected CSV creates a new version; findings stay tied to original data
- Ownership/privacy: only own files/runs/charts/sessions; UI shows retention and allows deleting raw upload and derived artifacts; sensitive columns not unnecessarily sent to LLM
- Trustworthy behaviour: explanations from computed output; results separate metrics/charts from AI interpretation
- Operational visibility: inspect upload -> job -> tools -> outcome -> LLM response; user-friendly errors, detailed developer logs

## 4. Async Architecture
- Chain: FastAPI -> Redis queue -> Celery worker -> EDA pipeline
- FastAPI validates, creates and tracks runs; Redis holds pending work and cache; worker does slow compute; Postgres is source of truth
- Workers are not "the agent"; they let tool work outlive the HTTP request
- One framework: Celery only (not RQ); WebSockets only (no SSE) in V1
- Heavy-request flow: create analysis_runs row (queued/pending) -> enqueue in Redis -> return run id -> worker runs pipeline -> saves metrics, charts, interpretation -> DB status completed/failed -> UI updates
- Lightweight actions (upload validation, row/column counts, schema display, single-column summary) stay synchronous; do not queue every tiny action

## 5. Run Submission (from backendV1 4a)
- Persist the job before doing any compute: create analysis_runs row plus one tool_executions row per selected tool
- Submission response is lightweight: id, status, execution_mode, dataset_version_id, created_at; full metrics/output come from GET /analysis-runs/{run_id} (and /results)
- Inline vs queued heuristic (deterministic):
  - inline only if exactly one tool, no plots, tool is not relationships, and active dataset version is within inline_analysis_max_rows and inline_analysis_max_columns
  - queue for multi-tool runs, plot-generating runs, relationship/correlation runs, and datasets above inline limits
- Inline runs execute inside the API request after the row is persisted and may return completed or failed immediately
- Queued runs return status pending; Celery worker later calls the same persisted-run executor and updates Postgres
- If dispatch to the queue fails: mark the already-created run failed with error_json describing the dispatch failure
- Same executor function serves inline and worker paths
- Status vocabulary caveat: design docs say queued; submission contract says pending; pick one (or treat both as active) and keep frontend isActiveRunStatus consistent

## 6. Final Component List
- Next.js frontend: upload, workspaces/history, results, live updates
- FastAPI API: auth, uploads, workspace/session APIs, analysis requests, results, WebSockets
- WebSockets: queued/running/completed/failed and progress events
- Celery workers: expensive EDA/agent jobs independent of the browser
- Redis: Celery broker, short-lived cache, live progress events
- PostgreSQL: users, workspaces, datasets, versions, sessions, runs, messages, tool calls, statuses
- Cloudflare R2: uploaded CSVs and generated charts (local mounted/MinIO storage in dev)
- EDA tool layer: deterministic functions
- Agent orchestration layer: LLM chooses valid tools and explains outputs
- Session/context retrieval: schema, selected columns, prior runs, compact conversation context
- Caching layer: dataset version + tool + parameters
- Celery retry policy: exponential backoff for transient failures only
- Auth + authorization with ownership checks
- Validation and limits
- Structured analysis records
- Logging and tracing
- Error handling with visible retry action
- Docker + Docker Compose
- Tests and small evaluation set
- CI/CD

## 7. Agent Orchestration
- Hand-written orchestrator; LiteLLM only as provider abstraction; no LangChain/LangGraph in V1
- Flow: load workspace context -> LLM planner selects allowed tools -> validate Pydantic tool arguments -> run deterministic tools -> LLM interprets structured output -> save run, tool executions, results
- Planner output (plan): intent, requires_clarification, clarification_question, tools[] of {name, arguments, reason}
- Interpretation output: answer, key_findings[], limitations[], follow_up_questions[]
- Tool registry exposes only permitted tools; max 3 tools per run; max 2 LLM calls per run
- Planner model groq/llama-3.3-70b-versatile; interpreter model gemini/gemini-2.5-flash (configurable)
- Structured tool output stored separately from LLM text
- Assistant chat message content currently embeds findings after a "Key findings:" marker that the frontend parses; keep that format stable or move findings into structured fields (see open items)

## 8. API (base /api/v1)
### Auth (Google OAuth via Authlib; no register/login/refresh)
- GET /auth/google/login: redirect to Google
- GET /auth/google/callback: validate, find/create user, create session, redirect to FRONTEND_URL/workspaces
- POST /auth/logout: clear session (204)
- GET /auth/me: current user (id, email, name, avatar_url)
- Session in signed HTTP-only cookie (SessionMiddleware)

### Workspaces
- POST /workspaces; GET /workspaces
- GET /workspaces/{workspace_id}: returns workspace, datasets (each with dataset and current_version), recent_runs, chat history
- PATCH /workspaces/{workspace_id}: rename
- DELETE /workspaces/{workspace_id}: soft delete, 7-day recovery, access revoked immediately
- Restore endpoint required by lifecycle (create, list, open, rename, soft-delete, restore)

### Datasets and versions
- POST /workspaces/{workspace_id}/datasets: upload, validate, create version, return overview
- GET /datasets/{dataset_id}/overview: rows, columns, names, inferred types, validation status
- GET /workspaces/{workspace_id}/datasets: versions list
- DELETE /datasets/{dataset_id}: removes a version and derived artifacts
- First upload: create workspace then upload; corrected CSV in same workspace becomes a new version

### Analysis runs (one generic endpoint; no per-tool public endpoints)
- POST /datasets/{dataset_id}/analysis-runs: body {request, selected_columns?}; also used by the deterministic tool panel in the UI
- GET /analysis-runs/{run_id}: status, progress_stage, progress_percent, selected_tools_json, explanation, failure details
- GET /datasets/{dataset_id}/analysis-runs: newest first
- POST /analysis-runs/{run_id}/retry; POST /analysis-runs/{run_id}/cancel
- GET /analysis-runs/{run_id}/results: structured metrics keyed by tool name (plus a reserved _agent key), artifacts, cache_hit, interpretation
- GET /analysis-runs/{run_id}/artifacts: plot/table exports (must return usable URLs, not raw storage keys)

### Dataset chat
- POST /datasets/{dataset_id}/chat: body {content, active_columns?}; returns {user_message, assistant_message, analysis_run_id | null, plan | null, interpretation | null}
- POST /datasets/{dataset_id}/messages: persist a message {role, content, analysis_run_id?}
- GET /datasets/{dataset_id}/messages: returns {conversation, messages}
- GET /datasets/{dataset_id}/question-usage: {conversation_id, used, limit, remaining}
- Follow-ups load relevant prior run metadata/results; never send the whole raw dataframe to the LLM
- Conversation object: id, workspace_id, dataset_version_id, active_columns_json, created_at, updated_at
- Message object: id, conversation_id, role (user|assistant|system), content, analysis_run_id, created_at

### Real time and ops
- WS /ws/workspaces/{workspace_id}: upload validation, queued/running, progress, completion, failure
- Events: analysis.progress {run_id, stage}, analysis.completed {run_id}; planned analysis.failed/queued
- Reconnect: restore from GET /analysis-runs/{run_id} or GET /workspaces/{workspace_id}
- GET /health; GET /ready (Postgres and Redis)
- Redis/Celery/cache have no user-facing endpoints

## 9. Database Schema (PostgreSQL)
General rules:
- UUID primary keys; index every foreign key; JSONB for flexible data; timestamptz everywhere
- Types for tables other than users are proposed from the design docs; verify against SQLAlchemy models
- Postgres never stores DataFrames or files; only object keys and metadata

### users
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default uuid4 |
| google_sub | varchar(255) | unique, indexed, not null |
| email | varchar(320) | unique, indexed, not null (stored lowercase) |
| name | varchar(255) | nullable |
| avatar_url | varchar(2048) | nullable |
| created_at | timestamptz | server default now(), not null |
| updated_at | timestamptz | server default now(), onupdate now(), not null |

### workspaces
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK users.id, indexed |
| title | varchar | not null |
| last_activity_at | timestamptz | updated on upload, analysis, message, open |
| deleted_at | timestamptz | nullable (soft delete) |
| scheduled_deletion_at | timestamptz | nullable; set on inactivity/user delete, +7 days recovery |
| created_at, updated_at | timestamptz | not null |

### datasets
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK workspaces.id, indexed |
| name | varchar | not null |
| current_version_id | UUID | FK dataset_versions.id, nullable (active version) |
| created_at | timestamptz | not null |

### dataset_versions (immutable)
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| dataset_id | UUID | FK datasets.id, indexed |
| version_number | int | unique with dataset_id |
| original_filename | varchar | |
| storage_key | varchar | R2 object key |
| checksum | varchar | |
| file_size | bigint | |
| row_count, column_count | int | |
| schema_json | JSONB | column names/types overview |
| validation_status | varchar | e.g. pending/valid/invalid |
| validation_error | text | nullable |
| created_at | timestamptz | not null |

### conversations
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK, indexed |
| dataset_version_id | UUID | FK, indexed |
| active_columns_json | JSONB | selected columns |
| created_at, updated_at | timestamptz | |

### messages
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| conversation_id | UUID | FK, indexed with created_at |
| role | varchar | user / assistant / system |
| content | text | |
| analysis_run_id | UUID | FK analysis_runs.id, nullable |
| created_at | timestamptz | |

### analysis_runs
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK, indexed |
| dataset_version_id | UUID | FK, indexed with status |
| conversation_id | UUID | FK, nullable |
| user_request | text | |
| status | varchar | pending/queued, running, completed, failed, cancelled |
| execution_mode | varchar | inline or queued |
| celery_task_id | varchar | nullable |
| cache_key | varchar | indexed; "analysis:" + sha256 |
| cache_hit | boolean | default false |
| source_run_id | UUID | FK analysis_runs.id, nullable (reused run) |
| agent_plan_json | JSONB | planner output |
| selected_tools_json | JSONB | list of {name, arguments, reason} |
| progress_stage | varchar | nullable |
| progress_percent | int | 0-100 |
| error_message | text | user-facing |
| error_json | JSONB | developer detail (e.g. dispatch failure) |
| started_at, completed_at | timestamptz | nullable |
| created_at, updated_at | timestamptz | |

### tool_executions
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| analysis_run_id | UUID | FK, indexed |
| tool_name | varchar | |
| arguments_json | JSONB | validated arguments |
| status | varchar | pending/running/completed/failed |
| result_json | JSONB | structured output |
| duration_ms | int | |
| error_message | text | |
| created_at | timestamptz | |

### artifacts
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| analysis_run_id | UUID | FK, indexed |
| tool_execution_id | UUID | FK, nullable |
| artifact_type | varchar | plot / table / export |
| storage_key | varchar | R2 key |
| mime_type | varchar | |
| created_at | timestamptz | |

### analysis_events (optional, recommended for tracing)
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| analysis_run_id | UUID | FK, indexed |
| stage | varchar | |
| message | text | |
| created_at | timestamptz | |

Key indexes: workspaces(user_id); dataset_versions(dataset_id, version_number) unique; analysis_runs(dataset_version_id, status); analysis_runs(cache_key); messages(conversation_id, created_at); every FK
- Relationship chain: User -> Workspace -> Dataset -> DatasetVersion -> Conversations / AnalysisRuns -> ToolExecutions / Artifacts

## 10. Locked V1 Decisions
- Dataset versions: logical dataset plus immutable version per upload; never overwrite file, schema, runs, artifacts; workspace marks one active version
- Retention: inactive after 30 days; scheduled_for_deletion; 7 days to restore; daily Celery Beat deletes Postgres rows and R2 objects; user delete follows same path with immediate access revocation
- Limits: CSV only; 25 MB; 200,000 rows; 100 columns; Celery concurrency 1; max 2 queued/running jobs per user; max 3 tools per run; 5-minute hard timeout (240s soft) with partial results saved; 2 LLM calls per run; 10 chat questions per conversation; sample rows to LLM max 20
- Retry: only 429, network timeouts, provider 5xx; 3 attempts, exponential backoff; never retry malformed CSVs, invalid columns, invalid tool arguments
- Cache: key = dataset_version_id + tool_name + normalized_tool_arguments + tool_version (sha256); Redis TTL 24h; Postgres keeps completed runs indexed by cache_key; Redis hit -> instant; Redis miss + Postgres match -> reuse and repopulate; new version or args -> recompute; record cache_hit and source_run_id; Redis failure never fails an analysis
- WebSocket recovery: live progress only; Postgres authoritative; persist status, progress_stage, progress_percent, updated_at, failure reason; REST restore first, then reconnect with backoff; no polling while socket healthy; no token streaming
- LLM privacy: never send entire CSV (overrides the original "feed dataframe to LLM"); aggregates only for standard tools; free-form questions pick a deterministic tool first; row-level context only as bounded PII-masked sample (max 20 rows, relevant columns); raw files stay in R2

## 11. Logging, Tracing and Observability
### Implemented/specified
- core/logging.py: structlog JSON logs to stdout; stdlib logging routed through ProcessorFormatter; ISO UTC timestamps, level, logger name; contextvars merged (hook for correlation IDs); configure_logging is idempotent; level from LOG_LEVEL
- core/exceptions.py: unhandled exceptions logged with method and path; known errors return {"error": {code, message, details}}
- main.py lifespan logs startup/shutdown with app name and environment
- DB-level trace: analysis_runs (request, plan, status, errors), tool_executions (arguments, result, duration, errors), artifacts, messages linked via analysis_run_id; optional analysis_events for stage history
- Health/readiness endpoints report Postgres/Redis status
- Dependencies listed for OpenTelemetry (api, sdk, FastAPI instrumentation)
### Required behaviour
- Trace path: upload -> job -> selected tools -> tool outcome -> LLM response; user-facing errors understandable, developer logs detailed
- Log: upload failures, parsing errors, tool failures, worker retries, dispatch failures, cache hit/miss, retention cleanup deletions
- Metrics wanted: latency per tool, failure rate, token/cost usage, cache hit rate, dataset size distribution
### Not yet wired (gaps)
- Request ID middleware binding to structlog contextvars; run_id/task_id binding inside Celery tasks
- ExtraAdder (or structured logger usage) so extra={"method","path"} fields actually appear in JSON logs
- LLM call logging (model, tokens, latency, cost, retries) via LiteLLM callbacks
- OpenTelemetry spans around planner, tools, interpreter, storage calls
- Log redaction of sensitive data; no raw dataset values in logs
- analysis_events table and logs for retention cleanup and cache decisions

## 12. Error Handling
- Exception classes: AppError base, NotFoundError 404, PermissionDeniedError 403, ConflictError 409; handlers for HTTPException, RequestValidationError (422), and unhandled 500
- Retry only transient external failures; permanent failures surface message plus retry action
- Dispatch failure marks run failed with error_json
- Graceful fallback: partial tool results saved on timeout or failure

## 13. Security and Reliability
- Treat uploads as untrusted; never execute anything derived from files; safe parsing and encoding handling
- Enforce size/row/column/computation limits; validate agent arguments (columns, plot types, limits, sampling)
- Ownership checks on every endpoint via get_current_user and per-resource checks
- Rate-limit uploads/analysis once public; cache derived summaries not raw data

## 14. Infrastructure and Deployment
- Latest plan: frontend on Vercel; backend API plus separate Celery worker (and Beat for retention) on Render; Supabase Postgres (500 MB free); Redis Cloud; Cloudflare R2
- backendV1.md section 7 (EC2 Compose with Caddy/Nginx and in-VM Redis) is outdated; update it or remove it
- Dev: Docker Compose at project root with Postgres and Redis (MinIO optional); only environment URLs change per env
- Compose is local only; not deployed
- R2: 10 GB, 1M writes, 10M reads, free egress, S3-compatible via boto3; storage abstraction: upload_dataset, get_dataset, save_artifact, delete_workspace_files; keys users/{user_id}/datasets/{version}.csv and users/{user_id}/runs/{run_id}/plot.png
- Postgres alternatives considered: Neon, Supabase, Aiven; Render free Postgres expires after 30 days

## 15. Authentication Details
- Authlib OAuth client with Google discovery URL, scope openid email profile
- Callback requires sub and email; get_or_create_google_user updates profile and handles IntegrityError race; session cleared then user_id set
- get_current_user reads user_id from session, validates UUID, loads user, clears invalid session, 401 otherwise
- Google setup: Cloud Console project; consent screen External with test users; Web client; redirect URI http://localhost:8000/api/v1/auth/google/callback; JavaScript origins cannot contain paths; do not open callback manually; start from /auth/google/login
- GOOGLE_API_KEY (Gemini) separate from GOOGLE_CLIENT_ID/SECRET

## 16. Config (core/config.py)
- App: app_name, app_version, app_env, debug, docs_enabled, api_v1_prefix, log_level, is_production
- Frontend/CORS: frontend_url, cors_origins (JSON or comma-separated)
- Session: session_secret_key, session_cookie_name, session_max_age_seconds, session_same_site
- Google OAuth: google_client_id, google_client_secret, google_oauth_redirect_uri
- LLM: google_api_key, groq_api_key, planner_model, interpreter_model
- database_url, redis_url, cache_ttl_seconds
- R2: r2_endpoint_url, r2_access_key_id, r2_secret_access_key, r2_bucket_name, r2_region_name
- Limits: max_upload_size_mb, max_dataset_rows, max_dataset_columns, max_active_jobs_per_user, max_tools_per_run, max_llm_calls_per_run, max_questions_per_conversation, max_llm_sample_rows
- Inline heuristic: inline_analysis_max_rows, inline_analysis_max_columns
- Celery: worker_concurrency, soft/hard time limits, retry_max_attempts
- Retention: workspace_retention_days, workspace_recovery_days

## 17. Project Structure
- app/main.py: app creation, middleware, routers
- app/core/: config, security, logging, exceptions
- app/api/: router.py (add each new route module here), deps.py, routes/ (auth, workspaces, datasets, analysis, conversations, results, websocket, health)
- app/db/: session.py, base.py, models/ (user, workspace, dataset, conversation, analysis_run, tool_execution, artifact)
- app/schemas/: Pydantic request/response models; never return raw ORM objects
- app/services/: auth, workspace, dataset, analysis, context, storage, cache, event
- app/agent/: orchestrator, planner, prompts, contracts, interpreter
- app/eda_tools/: high_level, column, relationships, quality, plotting, registry
- app/workers/: celery_app, analysis_tasks
- app/integrations/: llm_client, oauth_client
- alembic/, tests/ (api, services, eda_tools, agent, workers), Dockerfile, docker-compose.yml, pyproject.toml, .env.example, README.md
- No repository layer initially

## 18. Dependencies
- fastapi, uvicorn[standard], pydantic-settings, python-multipart, orjson
- sqlalchemy, psycopg[binary], alembic
- authlib, httpx, itsdangerous
- celery[redis], redis, boto3
- pandas, numpy, pyarrow, matplotlib, seaborn, scipy
- litellm, tenacity
- structlog, opentelemetry-api, opentelemetry-sdk, opentelemetry-instrumentation-fastapi
- pytest, pytest-asyncio, pytest-cov, ruff, mypy
- scikit-learn only for optional baseline-model tool

## 19. Development Order and Status
- Order: env/deps -> Postgres+Redis+Alembic -> /health,/ready -> OAuth -> workspaces -> datasets/versions -> storage -> conversations -> EDA tools -> analysis runs -> cache -> Celery -> agent -> chat -> WebSockets -> journey tests -> Docker/CI/deploy
- Per slice: model -> schema -> service -> route -> migration -> register router -> test
- Status: backend runs locally (Postgres, Redis, Celery, R2 uploads, OAuth); workspaces, datasets, conversations/chat, analysis runs, results, EDA tools, WebSocket events working; frontend shows outputs via results endpoint

## 20. Open Items and Inconsistencies in the Source Docs
- Agent&Tooldesign.md still contains the rejected "persist a dataframe in DB" chat line
- backendV1.md has a stray "durin" at the end and the outdated EC2 deployment block
- Status naming: queued vs pending
- Product name: DataScope vs DataLens
- Restore workspace endpoint, retention Celery Beat task, rate limiting, and cancellation behaviour need confirmation in code
- Chat findings are parsed from message text; consider storing key_findings as structured fields
