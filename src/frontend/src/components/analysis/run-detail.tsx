"use client";

import Link from "next/link";
import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAnalysisRunActions } from "@/hooks/use-analysis-run";
import { useRunResults } from "@/hooks/use-run-results";
import { formatDateTime, formatDuration } from "@/lib/formatters";
import {
  isActiveRunStatus,
  isTerminalRunStatus,
  type AnalysisInterpretation,
  type AnalysisRun,
  type ArtifactItem,
  type ToolExecution,
} from "@/types/analysis";
import { CancelAnalysisButton } from "./cancel-analysis-button";
import { ChartGallery } from "./chart-gallery";
import { InterpretationPanel } from "./interpretation-panel";
import { ResultMetrics } from "./result-metrics";
import { RetryAnalysisButton } from "./retry-analysis-button";
import { RunStatus } from "./run-status";
import { ToolResultSection } from "./tool-result-section";

function collectArtifacts(
  executions: ToolExecution[],
  fromResults: ArtifactItem[] | undefined,
): ArtifactItem[] {
  if (fromResults && fromResults.length > 0) {
    return fromResults;
  }
  const embedded: ArtifactItem[] = [];
  for (const execution of executions) {
    const payloads = execution.result_json?.artifacts;
    if (!Array.isArray(payloads)) {
      continue;
    }
    for (const item of payloads) {
      if (item && typeof item === "object") {
        embedded.push({
          ...(item as ArtifactItem),
          tool_name: execution.tool_name,
        });
      }
    }
  }
  return embedded;
}

function humanizeRunError(
  errorJson: Record<string, unknown> | null | undefined,
): string | null {
  if (!errorJson) {
    return null;
  }
  if (typeof errorJson.message === "string") {
    return errorJson.message;
  }
  const tools = errorJson.tools;
  if (Array.isArray(tools) && tools.length > 0) {
    return `${tools.length} tool${tools.length === 1 ? "" : "s"} failed during this run.`;
  }
  return "This analysis run failed.";
}

function selectedToolNames(run: AnalysisRun): string[] {
  return (run.selected_tools_json ?? []).map((tool) =>
    String(tool.name ?? "tool").replaceAll("_", " "),
  );
}

export function RunDetail({
  run,
  workspaceId,
  onChanged,
}: {
  run: AnalysisRun;
  workspaceId: string;
  onChanged?: () => void;
}) {
  const { retryRun, cancelRun, isMutating, error } = useAnalysisRunActions();
  const {
    results,
    isLoading: isLoadingResults,
    error: resultsError,
    refresh: refreshResults,
  } = useRunResults(run.id, run.status);

  const isActive = isActiveRunStatus(run.status);
  const isTerminal = isTerminalRunStatus(run.status);

  const executions = useMemo(() => {
    if (run.tool_executions?.length) {
      return run.tool_executions;
    }
    return Object.entries(results?.metrics ?? {})
      .filter(([key]) => key !== "_agent")
      .map(([toolName, result], index) => ({
        id: `${run.id}-${toolName}-${index}`,
        analysis_run_id: run.id,
        tool_name: toolName,
        arguments_json: {},
        status: "completed",
        result_json:
          result && typeof result === "object"
            ? (result as Record<string, unknown>)
            : { value: result },
        error_json: null,
        timings_json: null,
        cache_hit: Boolean(run.cache_hit),
        created_at: run.created_at,
        started_at: run.started_at,
        completed_at: run.completed_at,
      }));
  }, [run, results?.metrics]);

  const artifacts = useMemo(
    () => collectArtifacts(executions, results?.artifacts),
    [executions, results?.artifacts],
  );

  const metricsSource =
    results?.metrics ??
    (run.results_json
      ? Object.fromEntries(
          Object.entries(run.results_json).filter(([key]) => key !== "_agent"),
        )
      : null);

  const explanation: AnalysisInterpretation | null =
    results?.explanation ??
    (
      run.results_json?._agent as
        | { interpretation?: AnalysisInterpretation }
        | undefined
    )?.interpretation ??
    null;

  const durationMs =
    typeof run.timings_json?.duration_ms === "number"
      ? run.timings_json.duration_ms
      : null;

  const completedTools = executions.filter(
    (item) => item.status === "completed",
  ).length;
  const totalTools = Math.max(
    executions.length,
    selectedToolNames(run).length,
    1,
  );
  const runError = humanizeRunError(results?.errors ?? run.error_json);
  const waitingForResults =
    isTerminal &&
    run.status === "completed" &&
    isLoadingResults &&
    !metricsSource;

  async function handleRetry() {
    await retryRun(run.id);
    onChanged?.();
  }

  async function handleCancel() {
    await cancelRun(run.id);
    onChanged?.();
  }

  return (
    <div className="mx-auto max-w-6xl space-y-5 px-5 py-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link
            className="text-xs font-medium text-blue-700 hover:underline"
            href={`/workspaces/${workspaceId}`}
          >
            ← Back to workspace
          </Link>
          <h1 className="mt-2 text-2xl font-semibold text-slate-950">
            Analysis results
          </h1>
          <p className="mt-1 text-sm capitalize text-slate-600">
            {selectedToolNames(run).join(" · ") || "Analysis run"}
          </p>
        </div>
        <RunStatus
          progress={run.progress_percent}
          stage={run.progress_stage}
          status={run.status}
        />
      </div>

      {isActive ? (
        <Card className="space-y-4 border-blue-200 bg-blue-50/60 p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-950">
                {run.status === "pending"
                  ? "Queued — waiting for a worker"
                  : "Running analysis tools"}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                {run.progress_stage
                  ? `Stage: ${run.progress_stage.replaceAll("_", " ")}`
                  : "Live progress updates as each tool finishes."}
                {typeof run.progress_percent === "number"
                  ? ` · ${Math.round(run.progress_percent)}%`
                  : ""}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Tools finished: {completedTools}/{totalTools}
              </p>
            </div>
            <CancelAnalysisButton
              isCancelling={isMutating}
              onCancel={() => void handleCancel()}
            />
          </div>
          <div className="h-2 overflow-hidden rounded bg-white/80">
            <div
              className="h-full bg-blue-600 transition-[width]"
              style={{
                width: `${Math.min(Math.max(run.progress_percent ?? 8, 8), 100)}%`,
              }}
            />
          </div>
          <Spinner label="Computing results..." />
        </Card>
      ) : null}

      <Card className="p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          Run summary
        </h2>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-xs text-slate-500">Created</dt>
            <dd className="mt-1 text-sm text-slate-900">
              {formatDateTime(run.created_at)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Completed</dt>
            <dd className="mt-1 text-sm text-slate-900">
              {isActive ? "In progress" : formatDateTime(run.completed_at)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Duration</dt>
            <dd className="mt-1 text-sm text-slate-900">
              {isActive ? "—" : formatDuration(durationMs)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Cache</dt>
            <dd className="mt-1 text-sm text-slate-900">
              {run.cache_hit ? "Reused earlier results" : "Fresh compute"}
            </dd>
          </div>
        </dl>

        <div className="mt-4">
          <p className="text-xs font-semibold text-slate-700">Selected tools</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {selectedToolNames(run).map((name) => (
              <span
                className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-700"
                key={name}
              >
                {name}
              </span>
            ))}
          </div>
        </div>

        {runError ? (
          <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
            {runError}
          </p>
        ) : null}

        {!isActive ? (
          <div className="mt-4">
            <RetryAnalysisButton
              isRetrying={isMutating}
              onRetry={() => void handleRetry()}
            />
          </div>
        ) : null}
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </Card>

      <Card className="space-y-4 p-5">
        <h2 className="text-base font-semibold text-slate-950">
          Headline metrics
        </h2>
        {waitingForResults ? (
          <Spinner label="Loading computed results..." />
        ) : isActive && !metricsSource ? (
          <Spinner label="Waiting for the first tool to finish..." />
        ) : metricsSource && Object.keys(metricsSource).length > 0 ? (
          <ResultMetrics metrics={metricsSource} />
        ) : isTerminal ? (
          <p className="text-sm text-slate-600">No results were produced.</p>
        ) : (
          <Spinner label="Results will appear here as tools complete..." />
        )}
        {resultsError ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-700">{resultsError}</p>
            <Button
              className="mt-2"
              onClick={() => void refreshResults().catch(() => undefined)}
              size="sm"
              variant="secondary"
            >
              Refetch results
            </Button>
          </div>
        ) : null}
      </Card>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-slate-950">
            Tool progress & outputs
          </h2>
          <p className="text-xs text-slate-500">
            {completedTools}/{totalTools} complete
          </p>
        </div>
        {executions.length === 0 ? (
          <Card className="p-5">
            {isActive ? (
              <Spinner label="Preparing tool executions..." />
            ) : (
              <p className="text-sm text-slate-600">
                No tool executions were recorded.
              </p>
            )}
          </Card>
        ) : (
          executions.map((execution) => (
            <ToolResultSection
              defaultExpanded={
                execution.status === "completed" || execution.status === "failed"
              }
              execution={execution}
              key={execution.id}
            />
          ))
        )}
      </div>

      {isActive && artifacts.length === 0 ? (
        <Card className="p-5">
          <Spinner label="Plots will appear here when available..." />
        </Card>
      ) : (
        <ChartGallery artifacts={artifacts} />
      )}

      {explanation ? <InterpretationPanel explanation={explanation} /> : null}
    </div>
  );
}
