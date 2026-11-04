
<a name="readme-top"></a>

<h1 align="left">
  <img src="../../assets/favicon.png" alt="DataScope logo" width="36" align="absmiddle">
  DataScope Frontend
</h1>


Next.js client for DataScope, a workspace-based EDA agent. It talks only to the FastAPI backend and does no analysis itself.

## Stack
- Next.js (App Router), React, TypeScript
- Tailwind CSS
- TanStack Query provider
- Fonts: Plus Jakarta Sans (body), Source Serif 4 (headings and brand), Inter (buttons), loaded from Google Fonts in `src/app/layout.tsx`

## Features
- Google sign-in, with avatar initials as the fallback when the photo fails to load
- Workspace list, with a collapsible sidebar that remembers its state
- CSV upload and a schema overview (rows, columns, types)
- Tabs for Schema, Analyses and History
- Deterministic tool panel and an analysis feed
- Live run progress over WebSockets
- Dataset chat on its own page, with expandable tool output and charts per answer
- Run detail page showing results, charts, cache status and timings
- Workspace settings (rename and delete)

## Routes
- `/login`: Google sign-in
- `/workspaces`: workspace list
- `/workspaces/[workspaceId]`: main workspace
- `/workspaces/[workspaceId]/chat`: dataset chat
- `/workspaces/[workspaceId]/runs/[runId]`: run results
- `/workspaces/[workspaceId]/settings`: rename and delete

## Project Structure
```text
src/
  app/          routes, layout, global styles, favicon
  components/
    layout/     topbar, sidebar, workspace shell
    workspace/  header, overview, schema table, tabs, upload, history
    analysis/   chat panel, analysis feed, tool panel, run status, charts
    ui/         button, card, badge, user avatar
  hooks/        auth, workspaces, conversation, run results, workspace events
  lib/          api client, websocket client, formatters
  types/        auth, workspace, dataset, analysis, conversation
  providers/    query provider
public/         static assets (favicon.png logo)
```

## Environment
Create `src/frontend/.env.local`:
```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/api/v1
```
- `NEXT_PUBLIC_*` values are baked in at build time. Rebuild after changing them.

## Run Locally
Start the backend, Postgres, Redis and the Celery worker first (see the root README).
```cmd
cd src/frontend
npm install
npm run dev
```
- App: http://localhost:3000
- The backend must allow `http://localhost:3000` in `CORS_ORIGINS`, and all requests are sent with cookies.

## Scripts
- `npm run dev`: development server
- `npm run build`: production build
- `npm run start`: serve the production build
- `npm run lint`: lint


## Notes
- Plots are served by backend-provided URLs and not read from storage directly.
- The sidebar collapse state is saved in `localStorage`.
- The frontend never holds secrets or calls LLM providers.