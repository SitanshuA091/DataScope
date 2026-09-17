**Account and workspace**
- A signed-in user can see their earlier datasets and analysis workspaces.
- Each uploaded dataset becomes a workspace containing its schema, conversations, analysis runs, charts, and findings.
- Users can rename, reopen, or delete a workspace.

**Upload and dataset readiness**
- User uploads a CSV and receives immediate confirmation that it is being validated/processed.
- For small files, the schema overview can appear quickly; for larger files, the UI shows a processing state rather than freezing.
- If parsing fails due to encoding, malformed rows, unsupported format, or limits, the user gets an actionable error.

**Resumable analysis sessions**
- A user may close the tab halfway through an analysis and later reopen the same workspace.
- The application restores completed results, current chat context, selected columns, and the last known status of an in-progress request.
- An incomplete request is visibly marked as queued, running, completed, failed, or cancelled—not silently lost.
- The user can retry a failed analysis without recreating the entire workspace.

**Background analysis scenarios**
- The user asks for a correlation heatmap across many columns, a detailed quality report, multiple high-cardinality distributions, or a baseline model.
- These should run independently of the browser request, report progress, and save their result when complete.
- The user should be able to navigate elsewhere, close the tab, or inspect an earlier result while the work continues.
- If a worker fails transiently, the system can retry; if it fails permanently, the user sees the failure and a retry option.

**Fast interactions vs queued work**
- “What are the columns and their types?” and a single numeric describe() should feel near-instant.
- A dataset-wide quality scan, large plot generation, or a model-training request may need a job status/progress UI.
- This prevents the user experience from feeling like one long chatbot loading spinner.
Cached-result scenarios
- User requests a high-level EDA, then asks for it again or revisits the workspace later: reuse the existing result.
- User explores age, goes away, then returns to age: reuse its calculated statistics and plot artifacts where still valid.
- If the same underlying dataset or analysis parameters have changed, the system should clearly treat it as a new result rather than serve stale data.
- Caching exists to make repeat exploration fast and control repeated compute/LLM cost—not merely as an infrastructure checkbox.

**Analysis history and reproducibility**
- Every completed investigation should have a record of:
  - user request,
  - agent-selected tool(s),
  - tool parameters,
  - structured statistical output,
  - generated plots,
  - final LLM explanation,
  - timestamp and status.
- A user should be able to answer: “How did the app reach this conclusion?” without relying only on chat text.
- This also lets them reopen a prior result instead of asking again.

**Conversation and context handling**
- The agent should understand references such as “compare that with salary” or “show the missing values for the previous columns.”
- The system stores a compact session context: current dataset, active columns, earlier completed analyses, and conversation history.
- It should not blindly stuff every old tool result into every LLM prompt; retrieve only relevant previous analysis context.

**Dataset versions**
- If a user uploads a corrected/revised CSV, it should create a new dataset version or new workspace.
- Prior findings must remain associated with the original data, so conclusions are not mixed across files. This matters even in a demo because users often fix missing values and re-upload.

**Result ownership and privacy**
- A user can access only their own files, runs, charts, and analysis sessions.
- The UI should make it clear when a dataset is retained and allow deletion of both raw upload and derived artifacts.
- Sensitive columns should not be unnecessarily sent to the LLM; summaries/samples can be controlled later.

**Trustworthy agent behaviour**
- The agent explains findings based on computed tool output, not invented values.
- Results visibly separate: computed metrics / chart and AI interpretation.
- If the request is ambiguous—“find issues”—the agent can run a quality-oriented investigation; if it needs a specific column that does not exist, it asks or states the limitation.

**Operational visibility**
- When something goes wrong, you should be able to inspect the request path: upload → job → selected tools → tool outcome → LLM response.
- This supports debugging real failure cases such as a malformed dataset, tool timeout, queue failure, or invalid agent parameters.
- User-facing failures should be understandable; developer-facing logs/traces should be detailed.
Useful demo boundary
- V1 should demonstrate persistence, resumability, controlled tools, background work for genuinely expensive tasks, cached repeat analysis, history, and transparent results.

**Not required** :-
- collaborative workspaces, scheduled analyses, many file type options

