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
  tool_executions: Array<Record<string, unknown>>;
};

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
