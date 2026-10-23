# DataScope — Frontend Design (consolidated)

Merges: frontenddesign (v2), frontenddesign1 (structure), frontendlayoutdesign, plus the chat-page redesign and fixes made during implementation.

## 1. Principles
- Frontend is a client of FastAPI only; no second API, business logic, statistics, or LLM calls; no secrets in the browser
- Feels like a durable analysis workspace with an agent chat, not a chatbot with a spinner
- Computed metrics/charts shown first; AI interpretation visibly separate beneath
- Postgres via REST is authoritative; WebSocket only triggers refreshes

## 2. Stack and Setup
- Next.js (App Router) + TypeScript + Tailwind CSS; npm; `src/` directory; alias "@/*"
- Create: `npx create-next-app@latest frontend --ts --tailwind --eslint --app --src-dir --use-npm --import-alias "@/*"`
- frontend/ sits next to backend/; run with `npm run dev` at http://localhost:3000
- Dependencies: @tanstack/react-query, lucide-react, clsx, tailwind-merge; recharts optional
- .env.local: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1, NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/api/v1
- Backend CORS must allow http://localhost:3000 with credentials; all API calls send cookies
- Note: current hooks (useConversation, useWorkspaceDetail, useRunResults) use local state with `apiFetch`, not TanStack Query; the provider exists but is not required by them

## 3. Routes
- /login: Google sign-in (full-page redirect to backend /auth/google/login)
- /workspaces: workspace list, create/upload
- /workspaces/[workspaceId]: main workspace (header, overview, tabs, upload, active runs)
- /workspaces/[workspaceId]/chat: dataset chat page (new; chat no longer lives on the workspace page)
- /workspaces/[workspaceId]/runs/[runId]: full run detail and reproducibility
- /workspaces/[workspaceId]/settings: rename/delete
- /: redirect by auth state; not-found page

## 4. Folder Structure (responsibilities)
- app/layout.tsx: providers and shell
- app/login/page.tsx, app/workspaces/page.tsx, app/not-found.tsx
- app/workspaces/[workspaceId]/page.tsx: workspace page
- app/workspaces/[workspaceId]/chat/page.tsx: chat page (new)
- app/workspaces/[workspaceId]/runs/[runId]/page.tsx: run detail
- app/workspaces/[workspaceId]/settings/page.tsx
- components/layout/: app-sidebar (workspace nav, user menu), topbar, workspace-shell (Topbar + sidebar + main)
- components/workspace/: workspace-header, dataset-overview, schema-table, upload-zone, workspace-tabs (Schema/Analyses/History), history-panel
- components/analysis/:
  - chat-panel: conversation UI (full-height, used on chat page)
  - analysis-feed: list of runs for the workspace
  - deterministic-tool-panel: run tools directly without chat
  - run-status: status badge with stage and percent
  - tool-response-viewer: renders one tool's metrics
  - chart-gallery: artifact images
  - plus planned: analysis-card, interpretation-panel, retry/cancel buttons, per-tool renderers
- components/ui/: Button, Card, Badge, and other primitives
- lib/: api-client (apiFetch), websocket, formatters (formatDateTime), constants
- hooks/: use-auth, use-workspaces (useWorkspaceDetail), use-conversation, use-run-results, use-workspace-events, use-analysis-run
- types/: auth, workspace, dataset, analysis (isActiveRunStatus), conversation
- providers/query-provider.tsx

## 5. Screen Layout (described)
- Top bar with product name and user menu; left sidebar listing workspaces with "+ New upload"
- Workspace page: header (title, last activity, dataset status badge, Chat and Settings buttons), dataset overview (rows, columns, type), tabs Schema / Analyses / History
- Main area: upload zone plus "Live updates: <status>" indicator; active analysis card list; tab content
- Analyses tab: deterministic tool panel above the analysis feed
- Chat page: header strip with workspace title, "Dataset chat" label and "Back to workspace" link; scrolling message area; input fixed at bottom of the page area
- Chat entry point is a button in the workspace header, enabled only when dataset status is ready

## 6. Types and Backend Contracts Used
- Message: id, conversation_id, role (user|assistant|system), content, analysis_run_id | null, created_at
- Conversation: id, workspace_id, dataset_version_id, active_columns_json, created_at, updated_at
- MessageListResponse: {conversation, messages}
- QuestionUsage: {conversation_id, used, limit, remaining}
- ChatResponse: {user_message, assistant_message, analysis_run_id, plan, interpretation}
  - plan: intent, requires_clarification, clarification_question, tools[{name, arguments, reason}]
  - interpretation: answer, key_findings[], limitations[], follow_up_questions[]
- Workspace detail: workspace, datasets[{dataset, current_version}], recent_runs
- Run fields used by UI: id, status, created_at, progress_percent, progress_stage, selected_tools_json
- Run results: metrics keyed by tool name plus reserved `_agent` key (excluded from tool tabs), artifacts[], cache_hit
- isActiveRunStatus must cover every active status the backend emits (pending/queued/running)

## 7. Workspace Page Behaviour
- Loads via useWorkspaceDetail; handles loading, error, not found
- Active dataset = detail.datasets[0]; datasetId from dataset.id; status "ready" when current_version exists
- WebSocket events (useWorkspaceEvents) trigger refresh(); connection status shown in the page
- "Active analysis" card lists runs where isActiveRunStatus is true; each opens the run detail route and shows RunStatus with progress
- Upload completes -> switch to Schema tab and refresh
- Analyses tab: DeterministicToolPanel (submits and refreshes) plus AnalysisFeed
- History tab: HistoryPanel
- Chat panel removed from the bottom of this page

## 8. Chat Page and ChatPanel Changes
- Motivation: sticky bottom chat panel removed from workspace page; chat becomes a dedicated page opened from a header button
- New file: app/workspaces/[workspaceId]/chat/page.tsx
  - uses useWorkspaceDetail and useWorkspaceEvents (refresh on events)
  - derives datasetId and active job count from recent_runs via isActiveRunStatus
  - renders WorkspaceShell, a header strip with back link, and ChatPanel in a full-height flex column (h-[calc(100vh-4rem)])
- workspace page.tsx: ChatPanel import and usage deleted
- workspace-header.tsx: Chat button added before Settings; blue link when ready, grey disabled span otherwise
- Header bug fixed: replacement block had been pasted inside the Settings `<Link>`, nesting `<a>` in `<a>` (hydration error) and duplicating the Badge; corrected to Badge, Chat, Settings as siblings
- chat-panel.tsx changes:
  - removed sticky wrapper, shadow, fixed 56/96 heights, isExpanded state and expand/collapse toggle
  - root is `flex min-h-0 flex-1 flex-col`; message area `min-h-0 flex-1 overflow-y-auto`; input bar at the bottom with max-w-4xl centering
  - status strip shows analyst indicator and used/limit question counter
  - handleSend now also blocks when the active job limit (2) is reached, so quick prompts cannot bypass it; error catch intentionally empty because useConversation exposes the error
  - empty state keeps the four quick prompts
  - unchanged: parseAssistantContent, MessageToolPreview, ChatMessage, QUICK_PROMPTS
- Message rendering:
  - user messages right-aligned blue; assistant messages left-aligned with "AI Analyst" label
  - assistant content split at the "Key findings:" marker into main text and a Key Findings list
  - if analysis_run_id exists: expandable "View computed tool output & charts" section that loads useRunResults only when expanded, shows cached badge, tool tabs (excluding `_agent`), ToolResponseViewer, ChartGallery, and a "Full run details" link to the run page
- useConversation behaviour:
  - loads messages and question usage in parallel on dataset change
  - sendChat adds an optimistic user message, calls POST /datasets/{id}/chat with {content, active_columns}, refreshes, and removes the optimistic message on error
  - saveMessage posts to /datasets/{id}/messages and refreshes
  - exposes messages, usage, isLoading, isSending, error, refresh, saveMessage, sendChat
- Chat page limits: input disabled at question limit or while sending; send disabled at job limit; placeholder text reflects no dataset, question limit, or ready state

## 9. Results Display
- Inline in chat: expandable tool output per assistant message
- Workspace: AnalysisFeed and run cards by status
- Run detail page: all tools, parameters, tables, plots, timings, errors, retry, reproducibility (request, selected tools, parameters, timestamps, status)
- Run card states: queued/pending (cancel), running (stage + progress, cancel), completed (metrics/charts first, interpretation below), failed (error, partial results, retry), cancelled (retry), completed with no output (explicit empty message), fetch error (inline retry)
- Computed output and AI interpretation in separate labelled sections; cache indicator when cache_hit
- Fallback JSON viewer for tools without a renderer so output is never invisible

## 10. Artifacts and Plots
- Plots live in private R2; UI uses backend-provided URLs only (signed URL or proxy)
- Signed URLs expire; refetch on error; do not store long-term
- Allow image host in next.config.ts remotePatterns or use plain img tags
- R2 CORS only needed when fetching image bytes with JavaScript

## 11. Real-Time and Recovery
- WS /ws/workspaces/{workspace_id}; events trigger REST refresh; no payload reliance
- On load/reconnect: REST first, then socket; reconnect with exponential backoff; fallback polling only when socket is down
- Connection status surfaced in the workspace page

## 12. Auth and Navigation Flow
- Login -> Google -> backend callback -> /workspaces -> open workspace (dataset retained) -> run tools or open Chat -> view results -> history/run detail
- 401 from any call redirects to /login; logout calls POST /auth/logout

## 13. Error Handling and Logging (frontend)
- apiFetch should surface backend error shape {error: {code, message, details}} as readable messages
- Visible states for loading, error, empty, disabled (no dataset, limits)
- Current logging: none dedicated; hooks store error strings in state; chat send errors shown under the input
- Recommended: central error logger in api-client (status, path, request id) using console in dev and an error-reporting service later; log WebSocket connect/disconnect events; send backend request id header if added

## 14. Build Order and Status
- Done: login, workspaces list, dataset retention on reopen, upload, schema overview, tool progress, results display, chat with tool output previews, chat moved to its own page
- Remaining: per-tool renderers polish, interpretation panel, retry/cancel buttons, run detail reproducibility panel, WebSocket-driven cache updates, workspace restore UI, retention info in UI

## 15. Debug Checklist
- Results missing: check GET /analysis-runs/{id}/results in Network tab (not requested -> wiring; empty -> backend persistence; 4xx/5xx -> cookie or backend)
- Verify results JSON shape matches viewers; verify artifact URLs open in a new tab
- Verify assistant message has analysis_run_id; verify WebSocket completion triggers refresh
- Hydration errors: no nested anchors or interactive elements inside links

## 16. Deployment
- Vercel hosts frontend; set production API and wss URLs; match backend CORS, FRONTEND_URL and cookie settings (SameSite/secure for cross-site cookies)
- Local Compose is optional for the frontend
