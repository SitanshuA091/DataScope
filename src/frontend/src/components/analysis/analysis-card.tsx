"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAnalysisRunActions } from "@/hooks/use-analysis-run";
import { useRunResults } from "@/hooks/use-run-results";
import { formatDateTime } from "@/lib/formatters";
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

function toolLabel(run: AnalysisRun) {
  const tools = run.selected_tools_json ?? [];
  if (tools.length === 0) {
    return "Analysis run";
  }
  return tools
    .map((tool) => String(tool.name ?? "tool").replaceAll("_", " "))
    .join(", ");
}

function buildExecutionsFromMetrics(
  run: AnalysisRun,
  metrics: Record<string, unknown> | null | undefined,
): ToolExecution[] {
  if (run.tool_executions?.length) {
    return run.tool_executions;
  }
  if (!metrics) {
    return [];
  }
  return Object.entries(metrics)
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
}

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

export function AnalysisCard({
  run,
  workspaceId,
  onChanged,
  defaultExpanded = false,
  compact = false,
}: {
  run: AnalysisRun;
  workspaceId?: string;
  onChanged?: () => void;
  defaultExpanded?: boolean;
  compact?: boolean;
}) {
  const [expanded, setExpanded] = useState(
    defaultExpanded || isActiveRunStatus(run.status),
  );
  const { retryRun, cancelRun, isMutating, error } = useAnalysisRunActions();
  const {
    results,
    isLoading: isLoadingResults,
    error: resultsError,
    refresh: refreshResults,
  } = useRunResults(run.id, run.status);

  const isActive = isActiveRunStatus(run.status);
  const isTerminal = isTerminalRunStatus(run.status);
  const detailHref = workspaceId
    ? `/workspaces/${workspaceId}/runs/${run.id}`
    : null;

  const executions = useMemo(
    () => buildExecutionsFromMetrics(run, results?.metrics),
    [run, results?.metrics],
  );
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

  async function handleRetry() {
    await retryRun(run.id);
    onChanged?.();
  }

  async function handleCancel() {
    await cancelRun(run.id);
    onChanged?.();
  }

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="truncate text-base font-semibold capitalize text-slate-950">
            {toolLabel(run)}
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Created {formatDateTime(run.created_at)}
            {run.completed_at
              ? ` · Finished ${formatDateTime(run.completed_at)}`
              : ""}
          </p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
            {run.cache_hit ? (
              <span className="rounded bg-slate-100 px-2 py-0.5 text-slate-700">
                Reused from earlier run
              </span>
            ) : null}
            <span className="font-mono text-[11px] text-slate-400">
              {run.id.slice(0, 8)}
            </span>
          </div>
        </div>
        <RunStatus
          progress={run.progress_percent}
          stage={run.progress_stage}
          status={run.status}
        />
      </div>

      <div className="space-y-4 px-5 py-4">
        {isActive ? (
          <p className="text-sm text-slate-600">
            {run.status === "pending"
              ? "Queued — waiting for a worker."
              : "Running deterministic tools. Progress updates live."}
          </p>
        ) : null}

        {run.status === "cancelled" ? (
          <p className="rounded-md bg-slate-50 p-3 text-sm text-slate-600">
            This run was cancelled. Retry to queue it again.
          </p>
        ) : null}

        {run.status === "failed" || results?.errors || run.error_json ? (
          <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">
            {JSON.stringify(results?.errors ?? run.error_json)}
          </p>
        ) : null}

        {isTerminal && run.status === "completed" ? (
          <div className="space-y-3">
            {isLoadingResults && !metricsSource ? (
              <p className="text-sm text-slate-500">Loading results...</p>
            ) : metricsSource && Object.keys(metricsSource).length > 0 ? (
              <ResultMetrics metrics={metricsSource} />
            ) : (
              <p className="text-sm text-slate-600">
                No results were produced.
              </p>
            )}
            {!compact && artifacts.length > 0 && !expanded ? (
              <ChartGallery artifacts={artifacts.slice(0, 1)} />
            ) : null}
            {!compact ? (
              <InterpretationPanel explanation={explanation} />
            ) : null}
          </div>
        ) : null}

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

        {expanded && isTerminal ? (
          <div className="space-y-4 border-t border-slate-100 pt-4">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Computed tool output
              </h3>
              {executions.length === 0 ? (
                <p className="mt-2 text-sm text-slate-600">
                  No tool executions were recorded for this run.
                </p>
              ) : (
                <div className="mt-3 space-y-3">
                  {executions.map((execution) => (
                    <ToolResultSection
                      compact={compact}
                      execution={execution}
                      key={execution.id}
                    />
                  ))}
                </div>
              )}
            </div>
            <ChartGallery artifacts={artifacts} />
            <InterpretationPanel explanation={explanation} />
          </div>
        ) : null}

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 bg-slate-50 px-5 py-3">
        <div className="flex flex-wrap gap-2">
          {isTerminal ? (
            <Button
              onClick={() => setExpanded((value) => !value)}
              size="sm"
              variant="ghost"
            >
              {expanded ? "Hide details" : "Show tool outputs"}
            </Button>
          ) : null}
          {detailHref ? (
            <Link
              className="inline-flex min-h-8 items-center rounded-md px-3 text-xs font-medium text-blue-700 hover:bg-blue-50"
              href={detailHref}
            >
              View details
            </Link>
          ) : null}
        </div>
        <div className="flex gap-2">
          {isActive ? (
            <CancelAnalysisButton
              isCancelling={isMutating}
              onCancel={() => void handleCancel()}
            />
          ) : null}
          {!isActive ? (
            <RetryAnalysisButton
              isRetrying={isMutating}
              onRetry={() => void handleRetry()}
            />
          ) : null}
        </div>
      </div>
    </Card>
  );
}
