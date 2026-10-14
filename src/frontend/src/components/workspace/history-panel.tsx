"use client";

import Link from "next/link";
import { RunStatus } from "@/components/analysis/run-status";
import { Card } from "@/components/ui/card";
import { formatDateTime } from "@/lib/formatters";
import type { AnalysisRun } from "@/types/analysis";
import type { WorkspaceDetail } from "@/types/workspace";

export function HistoryPanel({
  detail,
  runs,
}: {
  detail: WorkspaceDetail;
  runs?: AnalysisRun[];
}) {
  const conversations = detail.conversations ?? [];
  const analysisRuns = runs ?? detail.recent_runs ?? [];

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-950">
            Analysis history
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Durable run records for this workspace. Open a run for full outputs.
          </p>
        </div>
        {analysisRuns.length === 0 ? (
          <p className="px-5 py-6 text-sm text-slate-600">
            No analysis runs yet. Use chat or the tools panel to create one.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {analysisRuns.map((run) => {
              const tools = (run.selected_tools_json ?? [])
                .map((tool) => String(tool.name ?? "tool").replaceAll("_", " "))
                .join(", ");
              return (
                <div
                  className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
                  key={run.id}
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium capitalize text-slate-950">
                      {tools || "Analysis run"}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      {formatDateTime(run.created_at)}
                      {run.cache_hit ? " · cache hit" : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <RunStatus
                      progress={run.progress_percent}
                      stage={run.progress_stage}
                      status={run.status}
                    />
                    <Link
                      className="text-xs font-medium text-blue-700 hover:underline"
                      href={`/workspaces/${detail.workspace.id}/runs/${run.id}`}
                    >
                      Open
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <Card className="overflow-hidden">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-950">
            Conversation history
          </h2>
        </div>
        {conversations.length === 0 ? (
          <p className="px-5 py-6 text-sm text-slate-600">
            No conversation history has been saved for this workspace yet.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {conversations.map((conversation, index) => (
              <div className="px-5 py-4" key={index}>
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm font-medium text-slate-950">
                    Conversation {index + 1}
                  </p>
                  <p className="text-xs text-slate-500">
                    {formatDateTime(
                      typeof conversation.conversation.updated_at === "string"
                        ? conversation.conversation.updated_at
                        : null,
                    )}
                  </p>
                </div>
                <p className="mt-2 text-sm text-slate-600">
                  {conversation.messages.length} saved messages
                </p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
