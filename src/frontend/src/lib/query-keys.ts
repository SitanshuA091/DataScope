/** Lightweight key helpers for local fetch/cache coordination (no React Query). */
export const queryKeys = {
  workspaces: ["workspaces"] as const,
  workspace: (workspaceId: string) => ["workspaces", workspaceId] as const,
  analysisRuns: (datasetId: string) =>
    ["datasets", datasetId, "analysis-runs"] as const,
  analysisRun: (runId: string) => ["analysis-runs", runId] as const,
  runResults: (runId: string) => ["analysis-runs", runId, "results"] as const,
  runArtifacts: (runId: string) =>
    ["analysis-runs", runId, "artifacts"] as const,
  messages: (datasetId: string) =>
    ["datasets", datasetId, "messages"] as const,
  questionUsage: (datasetId: string) =>
    ["datasets", datasetId, "question-usage"] as const,
};
