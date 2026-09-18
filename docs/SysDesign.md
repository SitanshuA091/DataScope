## Techmnical/Implementation Details
**Components to start off with**
FastAPI
Postgres
Redis
worker
frontend
Docker

**Components Finalized for system**
| Component                          | Usage                                                                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **React/Next.js frontend**         | Upload datasets, show workspaces/history, display charts/results, and receive live job updates.                                       |
| **FastAPI API**                    | Handles auth, uploads, workspace/session APIs, analysis requests, result retrieval, and WebSocket connections.                        |
| **WebSockets**                     | Pushes `queued/running/completed/failed` status and analysis-progress events to the active client.                                    |
| **Celery workers**                 | Run expensive EDA/agent jobs independently of the API request, even if the user closes the browser.                                   |
| **Redis**                          | Acts as Celery’s message broker and stores short-lived cached analysis results / possibly live progress events.                       |
| **PostgreSQL**                     | Persistent source of truth for users, workspaces, datasets, versions, sessions, runs, messages, tool calls, and statuses.             |
| **Dataset/file storage** (Cloudfare R2)          | Stores uploaded CSVs and generated chart files; use local mounted storage initially and object storage when deployed.                 |
| **EDA tool layer**                 | Deterministic functions for high-level EDA, column analysis, relationships, and data-quality checks.                                  |
| **Agent orchestration layer**      | Uses the LLM to choose valid tools and explain their structured outputs, while never letting it invent statistics.                    |
| **Session/context retrieval**      | Loads relevant dataset schema, selected columns, prior runs, and compact conversation context for follow-up requests.                 |
| **Caching layer**                  | Reuses results for the same dataset version + tool + parameters, reducing repeated compute and LLM cost.                              |
| **Celery retry policy**            | Use Celery retries with exponential backoff for transient LLM/API/network failures; do not retry malformed files or invalid requests. |
| **Authentication + authorization** | Login and ownership checks so users can access only their own workspaces, files, runs, and artifacts.                                 |
| **Validation and limits**          | Enforces allowed file types, size/row/column limits, safe parsing, and valid agent-selected tool arguments.                           |
| **Structured analysis records**    | Saves request, selected tools, parameters, metrics, plots, LLM explanation, timestamps, and final status for reproducibility.         |
| **Logging and tracing**            | Captures upload → queue → worker → tool calls → LLM response, making failures and agent decisions inspectable.                        |
| **Error handling**                 | Returns useful user errors for invalid CSVs, failed jobs, timeouts, and retries, with a visible retry action.                         |
| **Docker + Docker Compose**        | Runs API, worker, Redis, Postgres, and frontend consistently locally and makes deployment reproducible.                               |
| **Tests and small evaluation set** | Tests tool correctness and agent routing/grounded explanations against a few representative datasets and requests.                    |
| **CI/CD**                          | Runs tests/linting/build checks on pushes, then later deploys the containerized services.                                             |


