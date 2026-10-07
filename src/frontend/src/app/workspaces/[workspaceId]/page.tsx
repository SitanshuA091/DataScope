"use client";

import { use, useCallback, useState } from "react";
import { AnalysisCard } from "@/components/analysis/analysis-card";
import { ChatPanel } from "@/components/analysis/chat-panel";
import { DeterministicToolPanel } from "@/components/analysis/deterministic-tool-panel";
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

export default function WorkspacePage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = use(params);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("schema");
  const { detail, isLoading, error, refresh } = useWorkspaceDetail(workspaceId);
  const handleEvent = useCallback(() => {
    void refresh();
  }, [refresh]);
  const connectionStatus = useWorkspaceEvents(workspaceId, handleEvent);

  const selectedDataset = detail?.datasets[0] ?? null;
  const datasetId = selectedDataset?.dataset.id ?? null;
  const datasetStatus = selectedDataset?.current_version ? "ready" : "no dataset";
  const runningRuns =
    detail?.recent_runs.filter((run) =>
      ["pending", "running"].includes(run.status),
    ) ?? [];

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
                <section className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                  <p className="text-sm font-medium text-slate-950">
                    Active analysis
                  </p>
                  <div className="mt-3 grid gap-3">
                    {runningRuns.map((run) => (
                      <AnalysisCard
                        key={run.id}
                        onChanged={() => {
                          void refresh();
                        }}
                        run={run}
                      />
                    ))}
                  </div>
                </section>
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
                  />
                  {detail.recent_runs.length === 0 ? (
                    <Card className="p-5">
                      <h2 className="text-base font-semibold text-slate-950">
                        Analyses
                      </h2>
                      <p className="mt-2 text-sm text-slate-600">
                        Ask a question after uploading a dataset to create a
                        reusable analysis record.
                      </p>
                    </Card>
                  ) : (
                    detail.recent_runs.map((run) => (
                      <AnalysisCard
                        key={run.id}
                        onChanged={() => {
                          void refresh();
                        }}
                        run={run}
                      />
                    ))
                  )}
                </div>
              ) : null}

              {activeTab === "history" ? <HistoryPanel detail={detail} /> : null}
            </div>
          </div>

          <ChatPanel
            datasetId={datasetId}
            onSubmitted={() => {
              setActiveTab("analyses");
              void refresh();
            }}
          />
        </div>
      )}
    </WorkspaceShell>
  );
}
