import type { AnalysisRun } from "./analysis";
import type { DatasetListItem } from "./dataset";

export type Workspace = {
  id: string;
  user_id: string;
  title: string;
  last_activity_at: string;
  deleted_at: string | null;
  scheduled_deletion_at: string | null;
  created_at: string;
  updated_at: string;
};

export type WorkspaceListResponse = {
  workspaces: Workspace[];
};

export type WorkspaceDetail = {
  workspace: Workspace;
  datasets: DatasetListItem[];
  recent_runs: AnalysisRun[];
  conversations: Array<{
    conversation: Record<string, unknown>;
    messages: Array<Record<string, unknown>>;
  }>;
};
