"use client";

import { use, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { AnalysisFeed } from "@/components/analysis/analysis-feed";
import { ChatPanel } from "@/components/analysis/chat-panel";
import { DeterministicToolPanel } from "@/components/analysis/deterministic-tool-panel";
import { RunStatus } from "@/components/analysis/run-status";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Card } from "@/components/ui/card";
import { DatasetOverview } from "@/components/workspace/dataset-overview";
import { HistoryPanel } from "@/components/workspace/history-panel";
import { SchemaTable } from "@/components/workspace/schema-table";
import { UploadZone } from "@/components/workspace/upload-zone";
import { WorkspaceHeader } from "@/components/workspace/workspace-header";
import {
  WorkspaceTabs,
  type WorkspaceTab,
} from "@/components/workspace/workspace-tabs";
import { useWorkspaceEvents } from "@/hooks/use-workspace-events";
import { useWorkspaceDetail } from "@/hooks/use-workspaces";
import { formatDateTime } from "@/lib/formatters";
import { isActiveRunStatus } from "@/types/analysis";

export default function WorkspacePage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = use(params);
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("schema");
  const { detail, isLoading, error, refresh } = useWorkspaceDetail(workspaceId);
  const handleEvent = useCallback(() => {
    void refresh();
  }, [refresh]);
  const connectionStatus = useWorkspaceEvents(workspaceId, handleEvent);

  const selectedDataset = detail?.datasets[0] ?? null;
  const datasetId = selectedDataset?.dataset.id ?? null;
  const datasetStatus = selectedDataset?.current_version
    ? "ready"
    : "no dataset";
  const recentRuns = detail?.recent_runs ?? [];
  const runningRuns = recentRuns.filter((run) => isActiveRunStatus(run.status));

  return (
    <WorkspaceShell>
      {isLoading ? (
        <div className="p-6 text-sm text-slate-600">Loading workspace...</div>
      ) : error || !detail ? (
        <div className="p-6 text-sm text-red-600">
          {error ?? "Workspace not found."}
        </div>
      ) : (
        <div className="flex min-h-[calc(100vh-4rem)] flex-col">
          <WorkspaceHeader
            datasetStatus={datasetStatus}
            workspace={detail.workspace}
          />
          <DatasetOverview
            item={selectedDataset}
            onDeleted={() => {
              void refresh();
            }}
          />
          <WorkspaceTabs activeTab={activeTab} onChange={setActiveTab} />

          <div className="flex-1 overflow-auto bg-slate-50 px-5 py-5">
            <div className="mx-auto max-w-6xl space-y-5">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <UploadZone
                  workspaceId={detail.workspace.id}
                  onUploaded={() => {
                    setActiveTab("schema");
                    void refresh();
                  }}
                />
                <div className="shrink-0 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs text-slate-500">
                  Live updates: {connectionStatus}
                </div>
              </div>

              {runningRuns.length > 0 ? (
                <Card className="overflow-hidden border-blue-200 bg-blue-50/50">
                  <div className="border-b border-blue-100 px-5 py-3">
                    <p className="text-sm font-medium text-slate-950">
                      Active analysis
                    </p>
                    <p className="mt-1 text-xs text-slate-600">
                      Open a run to watch tool progress and outputs.
                    </p>
                  </div>
                  <div className="divide-y divide-blue-100">
                    {runningRuns.map((run) => {
                      const tools = (run.selected_tools_json ?? [])
                        .map((tool) =>
                          String(tool.name ?? "tool").replaceAll("_", " "),
                        )
                        .join(", ");
                      return (
                        <button
                          className="flex w-full flex-col gap-3 px-5 py-4 text-left transition hover:bg-blue-50 sm:flex-row sm:items-center sm:justify-between"
                          key={run.id}
                          onClick={() =>
                            router.push(
                              `/workspaces/${workspaceId}/runs/${run.id}`,
                            )
                          }
                          type="button"
                        >
                          <div>
                            <p className="text-sm font-semibold capitalize text-slate-950">
                              {tools || "Analysis run"}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              Started {formatDateTime(run.created_at)}
                            </p>
                          </div>
                          <div className="flex items-center gap-3">
                            <RunStatus
                              progress={run.progress_percent}
                              stage={run.progress_stage}
                              status={run.status}
                            />
                            <span className="text-xs font-medium text-blue-700">
                              Open →
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </Card>
              ) : null}

              {activeTab === "schema" ? (
                <SchemaTable item={selectedDataset} />
              ) : null}

              {activeTab === "analyses" ? (
                <div className="space-y-4">
                  <DeterministicToolPanel
                    datasetId={datasetId}
                    onSubmitted={() => {
                      void refresh();
                    }}
                    workspaceId={workspaceId}
                  />
                  <AnalysisFeed runs={recentRuns} workspaceId={workspaceId} />
                </div>
              ) : null}

              {activeTab === "history" ? (
                <HistoryPanel detail={detail} runs={recentRuns} />
              ) : null}
            </div>
          </div>
        </div>
      )}
    </WorkspaceShell>
  );
}
