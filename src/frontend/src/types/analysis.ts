export type AnalysisStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type ToolSelection = {
  name: string;
  arguments?: Record<string, unknown>;
};

export type AnalysisTool = {
  name: string;
  description: string;
  arguments: Record<string, unknown>;
};

export type AnalysisToolListResponse = {
  tools: AnalysisTool[];
};

export type ToolExecution = {
  id: string;
  analysis_run_id: string;
  tool_name: string;
  arguments_json: Record<string, unknown>;
  status: string;
  result_json: Record<string, unknown> | null;
  error_json: Record<string, unknown> | null;
  timings_json: Record<string, unknown> | null;
  cache_key?: string | null;
  cache_hit: boolean;
  source_execution_id?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
};

export type ArtifactItem = {
  id?: string;
  artifact_type: string;
  storage_key?: string | null;
  mime_type?: string | null;
  tool_name?: string | null;
  metadata?: Record<string, unknown>;
  url?: string | null;
  title?: string;
  columns?: string[];
  kind?: string;
};

export type AnalysisInterpretation = {
  answer?: string;
  key_findings?: string[];
  limitations?: string[];
  follow_up_questions?: string[];
  [key: string]: unknown;
};

/** Response from GET /analysis-runs/{id}/results */
export type RunResults = {
  run_id: string;
  status: AnalysisStatus | string;
  metrics: Record<string, unknown>;
  explanation: AnalysisInterpretation | null;
  artifacts: ArtifactItem[];
  errors: Record<string, unknown> | null;
  cache_hit: boolean;
  source_run_id: string | null;
};

export type ArtifactListResponse = {
  artifacts: ArtifactItem[];
};

export type AnalysisRunHistoryItem = {
  id: string;
  workspace_id: string;
  dataset_version_id: string;
  status: AnalysisStatus | string;
  selected_tools_json: Array<Record<string, unknown>>;
  error_json: Record<string, unknown> | null;
  progress_stage?: string | null;
  progress_percent?: number | null;
  cache_hit?: boolean;
  source_run_id?: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
};

export type AnalysisRunHistoryResponse = {
  analysis_runs: AnalysisRunHistoryItem[];
};

export type AnalysisRun = {
  id: string;
  workspace_id: string;
  dataset_version_id: string;
  request_json: Record<string, unknown>;
  selected_tools_json: Array<Record<string, unknown>>;
  status: AnalysisStatus | string;
  results_json: Record<string, unknown> | null;
  error_json: Record<string, unknown> | null;
  timings_json: Record<string, unknown> | null;
  cache_key: string | null;
  cache_hit: boolean;
  source_run_id: string | null;
  progress_stage: string | null;
  progress_percent: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
  tool_executions: ToolExecution[];
};

export const TERMINAL_RUN_STATUSES = new Set([
  "completed",
  "failed",
  "cancelled",
]);

export function isTerminalRunStatus(status: string | undefined | null) {
  return Boolean(status && TERMINAL_RUN_STATUSES.has(status));
}

export function isActiveRunStatus(status: string | undefined | null) {
  return status === "pending" || status === "running";
}

export type AnalysisRunSubmission = {
  id: string;
  status: AnalysisStatus;
  execution_mode: "inline" | "queued";
  dataset_version_id: string;
  created_at: string;
};

export type WorkspaceEvent = {
  type?: string;
  analysis_run_id?: string;
  status?: AnalysisStatus | string;
  progress_stage?: string | null;
  progress_percent?: number | null;
  [key: string]: unknown;
};
