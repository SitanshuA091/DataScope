import type { AnalysisRun } from "@/types/analysis";
import type { CurrentUser } from "@/types/auth";
import type { DatasetListItem } from "@/types/dataset";
import type { Workspace, WorkspaceDetail } from "@/types/workspace";

const now = "2026-10-07T09:30:00.000Z";

export const mockUser: CurrentUser = {
  id: "local-user",
  email: "local@datascope.dev",
  name: "Local Analyst",
  avatar_url: null,
  created_at: "2026-09-21T00:00:00.000Z",
};

export const mockWorkspaces: Workspace[] = [
  {
    id: "demo-sales",
    user_id: mockUser.id,
    title: "Sales performance CSV",
    last_activity_at: now,
    deleted_at: null,
    scheduled_deletion_at: null,
    created_at: "2026-10-01T04:15:00.000Z",
    updated_at: now,
  },
  {
    id: "demo-retention",
    user_id: mockUser.id,
    title: "Customer retention study",
    last_activity_at: "2026-10-06T16:20:00.000Z",
    deleted_at: null,
    scheduled_deletion_at: null,
    created_at: "2026-09-29T11:45:00.000Z",
    updated_at: "2026-10-06T16:20:00.000Z",
  },
  {
    id: "demo-ops",
    user_id: mockUser.id,
    title: "Operations quality audit",
    last_activity_at: "2026-10-05T13:10:00.000Z",
    deleted_at: null,
    scheduled_deletion_at: null,
    created_at: "2026-09-24T08:00:00.000Z",
    updated_at: "2026-10-05T13:10:00.000Z",
  },
];

const salesDataset: DatasetListItem = {
  dataset: {
    id: "dataset-sales-q4",
    workspace_id: "demo-sales",
    name: "q4_sales_pipeline.csv",
    current_version_id: "version-sales-q4",
    created_at: "2026-10-01T04:20:00.000Z",
    updated_at: now,
  },
  current_version: {
    id: "version-sales-q4",
    dataset_id: "dataset-sales-q4",
    version_number: 3,
    original_filename: "q4_sales_pipeline.csv",
    storage_key: "mock/q4_sales_pipeline.csv",
    checksum: "local-demo",
    file_size: 1843200,
    row_count: 12450,
    column_count: 18,
    validation_status: "valid",
    validation_error: null,
    created_at: now,
    schema_json: [
      { name: "opportunity_id", dtype: "string", missing_count: 0, nullable: false },
      { name: "region", dtype: "category", missing_count: 0, nullable: false },
      { name: "segment", dtype: "category", missing_count: 12, nullable: true },
      { name: "pipeline_value", dtype: "decimal", missing_count: 0, nullable: false },
      { name: "probability", dtype: "decimal", missing_count: 41, nullable: true },
      { name: "close_date", dtype: "date", missing_count: 6, nullable: true },
      { name: "sales_rep", dtype: "string", missing_count: 0, nullable: false },
      { name: "stage", dtype: "category", missing_count: 0, nullable: false },
    ],
  },
};

const runs: AnalysisRun[] = [
  {
    id: "run-quality",
    workspace_id: "demo-sales",
    dataset_version_id: "version-sales-q4",
    request_json: {
      question: "Check readiness before weekly pipeline review",
    },
    selected_tools_json: [
      { name: "schema_profile" },
      { name: "missingness_report" },
      { name: "outlier_scan" },
    ],
    status: "completed",
    results_json: {
      readiness_score: "94%",
      missing_cells: "59",
      outlier_rows: "27",
      duplicate_rows: "0",
      strongest_signal: "pipeline_value by region",
      recommendation: "Review missing probabilities before forecasting.",
    },
    error_json: null,
    timings_json: { total_seconds: 21.4, cache_source: "postgres" },
    cache_key: "mock-quality",
    cache_hit: true,
    source_run_id: null,
    progress_stage: "completed",
    progress_percent: 100,
    created_at: "2026-10-07T08:54:00.000Z",
    started_at: "2026-10-07T08:54:02.000Z",
    completed_at: "2026-10-07T08:54:23.000Z",
    updated_at: "2026-10-07T08:54:23.000Z",
    tool_executions: [],
  },
  {
    id: "run-segments",
    workspace_id: "demo-sales",
    dataset_version_id: "version-sales-q4",
    request_json: {
      question: "Find regional pipeline concentration",
    },
    selected_tools_json: [
      { name: "segment_summary", arguments: { group_by: "region" } },
      { name: "correlation_scan" },
    ],
    status: "running",
    results_json: {
      stage: "Computing regional aggregates",
    },
    error_json: null,
    timings_json: { queued_seconds: 2.1 },
    cache_key: null,
    cache_hit: false,
    source_run_id: null,
    progress_stage: "Running deterministic tools",
    progress_percent: 64,
    created_at: "2026-10-07T09:22:00.000Z",
    started_at: "2026-10-07T09:22:05.000Z",
    completed_at: null,
    updated_at: "2026-10-07T09:29:00.000Z",
    tool_executions: [],
  },
];

export function getMockWorkspaceDetail(workspaceId: string): WorkspaceDetail {
  const workspace =
    mockWorkspaces.find((item) => item.id === workspaceId) ?? mockWorkspaces[0];

  return {
    workspace,
    datasets: workspace.id === "demo-sales" ? [salesDataset] : [],
    recent_runs: workspace.id === "demo-sales" ? runs : [],
    conversations:
      workspace.id === "demo-sales"
        ? [
            {
              conversation: {
                id: "conversation-sales",
                updated_at: "2026-10-07T09:02:00.000Z",
              },
              messages: [
                { role: "user", content: "Check readiness for review." },
                { role: "assistant", content: "Readiness score is 94%." },
              ],
            },
          ]
        : [],
  };
}
