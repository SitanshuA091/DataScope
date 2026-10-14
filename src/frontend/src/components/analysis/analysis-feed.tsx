"use client";

import { useRouter } from "next/navigation";
import { RunStatus } from "@/components/analysis/run-status";
import { Card } from "@/components/ui/card";
import { formatDateTime } from "@/lib/formatters";
import type { AnalysisRun } from "@/types/analysis";

function toolLabel(run: AnalysisRun) {
  const tools = run.selected_tools_json ?? [];
  if (tools.length === 0) {
    return "Analysis run";
  }
  return tools
    .map((tool) => String(tool.name ?? "tool").replaceAll("_", " "))
    .join(", ");
}

export function AnalysisFeed({
  runs,
  workspaceId,
  emptyMessage = "Ask a question or run tools after uploading a dataset to create reusable analysis records.",
}: {
  runs: AnalysisRun[];
  workspaceId: string;
  onChanged?: () => void;
  emptyMessage?: string;
}) {
  const router = useRouter();

  if (runs.length === 0) {
    return (
      <Card className="p-5">
        <h2 className="text-base font-semibold text-slate-950">Analyses</h2>
        <p className="mt-2 text-sm text-slate-600">{emptyMessage}</p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-950">Analyses</h2>
        <p className="mt-1 text-sm text-slate-600">
          Open a run to watch progress and view computed outputs.
        </p>
      </div>
      <div className="divide-y divide-slate-100">
        {runs.map((run) => (
          <button
            className="flex w-full flex-col gap-3 px-5 py-4 text-left transition hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
            key={run.id}
            onClick={() =>
              router.push(`/workspaces/${workspaceId}/runs/${run.id}`)
            }
            type="button"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold capitalize text-slate-950">
                {toolLabel(run)}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {formatDateTime(run.created_at)}
                {run.cache_hit ? " · reused cache" : ""}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <RunStatus
                progress={run.progress_percent}
                stage={run.progress_stage}
                status={run.status}
              />
              <span className="text-xs font-medium text-blue-700">
                View results →
              </span>
            </div>
          </button>
        ))}
      </div>
    </Card>
  );
}
