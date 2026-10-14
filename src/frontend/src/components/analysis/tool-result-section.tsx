"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { formatDuration } from "@/lib/formatters";
import type { ToolExecution } from "@/types/analysis";
import { ToolResponseViewer } from "./tool-response-viewer";

function toolDurationMs(execution: ToolExecution): number | null {
  const duration = execution.timings_json?.duration_ms;
  return typeof duration === "number" ? duration : null;
}

function humanizeError(errorJson: Record<string, unknown> | null): string {
  if (!errorJson) {
    return "Tool failed.";
  }
  if (typeof errorJson.message === "string") {
    return errorJson.message;
  }
  if (typeof errorJson.error === "string") {
    return errorJson.error;
  }
  if (
    errorJson.error &&
    typeof errorJson.error === "object" &&
    errorJson.error !== null &&
    "message" in errorJson.error
  ) {
    return String((errorJson.error as { message: unknown }).message);
  }
  return "Tool failed while computing results.";
}

function meaningfulArgs(args: Record<string, unknown>) {
  return Object.entries(args).filter(([key, value]) => {
    if (key === "include_plots" || key === "artifact_dir") {
      return false;
    }
    return value !== undefined && value !== null && value !== "";
  });
}

export function ToolResultSection({
  execution,
  defaultExpanded = true,
}: {
  execution: ToolExecution;
  compact?: boolean;
  defaultExpanded?: boolean;
}) {
  const isPending =
    execution.status === "pending" || execution.status === "running";
  const [expanded, setExpanded] = useState(defaultExpanded && !isPending);
  const result =
    execution.result_json && typeof execution.result_json === "object"
      ? execution.result_json
      : null;
  const argEntries = meaningfulArgs(execution.arguments_json ?? {});

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <button
        className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left hover:bg-slate-50"
        onClick={() => setExpanded((value) => !value)}
        type="button"
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold capitalize text-slate-950">
              {execution.tool_name.replaceAll("_", " ")}
            </h3>
            <Badge
              variant={
                execution.status === "completed"
                  ? "success"
                  : execution.status === "failed"
                    ? "danger"
                    : "info"
              }
            >
              {execution.status}
            </Badge>
            {execution.cache_hit ? (
              <Badge variant="neutral">cache hit</Badge>
            ) : null}
          </div>
          {argEntries.length > 0 ? (
            <p className="mt-1 truncate text-xs text-slate-500">
              {argEntries
                .map(([key, value]) =>
                  Array.isArray(value)
                    ? `${key}: ${(value as unknown[]).join(", ")}`
                    : `${key}: ${String(value)}`,
                )
                .join(" · ")}
            </p>
          ) : (
            <p className="mt-1 text-xs text-slate-500">Default tool settings</p>
          )}
        </div>
        <div className="shrink-0 text-right">
          <p className="text-xs text-slate-500">
            {isPending ? "In progress" : formatDuration(toolDurationMs(execution))}
          </p>
          <p className="mt-1 text-xs font-medium text-slate-600">
            {expanded ? "Collapse" : "Expand"}
          </p>
        </div>
      </button>

      {expanded ? (
        <div className="space-y-3 border-t border-slate-100 px-4 py-4">
          {isPending ? (
            <Spinner label={`Running ${execution.tool_name.replaceAll("_", " ")}...`} />
          ) : null}
          {execution.error_json ? (
            <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">
              {humanizeError(execution.error_json)}
            </p>
          ) : null}
          {!isPending && result ? (
            <ToolResponseViewer data={result} toolName={execution.tool_name} />
          ) : null}
          {!isPending && !result && !execution.error_json ? (
            <p className="text-sm text-slate-500">
              No results were produced for this tool.
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
