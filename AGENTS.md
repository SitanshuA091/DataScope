# DataScope

## Project layout

- `src/backend/` contains the FastAPI API, database models and migrations, EDA tools, agent orchestration, and Celery workers.
- `src/frontend/` contains the Next.js application. Follow `src/frontend/AGENTS.md` for frontend-specific instructions.
- `docs/` contains product and system design documents. Check relevant docs when changing behavior covered by them.

## Development guidance

- Read the relevant service README before changing setup or service behavior: `src/backend/README.md` or `src/frontend/README.md`.
- Keep data analysis deterministic in backend tools; the LLM plans and explains results rather than serving as the source of computed facts.
- Keep API routes under `/api/v1` and preserve the backend's documented persistence and workspace boundaries.
- Do not commit secrets. Backend local configuration belongs in `src/backend/.env` (copy `.env.example`); frontend local configuration belongs in `src/frontend/.env.local`.
- Use the root README for local service startup and database setup.
