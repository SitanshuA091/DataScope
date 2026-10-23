"use client";

import Link from "next/link";
import { use, useCallback } from "react";
import { ChatPanel } from "@/components/analysis/chat-panel";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { useWorkspaceEvents } from "@/hooks/use-workspace-events";
import { useWorkspaceDetail } from "@/hooks/use-workspaces";
import { isActiveRunStatus } from "@/types/analysis";

export default function WorkspaceChatPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = use(params);
  const { detail, isLoading, error, refresh } = useWorkspaceDetail(workspaceId);
  const handleEvent = useCallback(() => {
    void refresh();
  }, [refresh]);
  useWorkspaceEvents(workspaceId, handleEvent);

  const datasetId = detail?.datasets[0]?.dataset.id ?? null;
  const activeJobCount = (detail?.recent_runs ?? []).filter((run) =>
    isActiveRunStatus(run.status),
  ).length;

  return (
    <WorkspaceShell>
      {isLoading ? (
        <div className="p-6 text-sm text-slate-600">Loading chat...</div>
      ) : error || !detail ? (
        <div className="p-6 text-sm text-red-600">
          {error ?? "Workspace not found."}
        </div>
      ) : (
        <div className="flex h-[calc(100vh-4rem)] flex-col">
          <div className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3">
            <div>
              <h1 className="text-lg font-semibold text-slate-950">
                {detail.workspace.title}
              </h1>
              <p className="text-xs text-slate-500">Dataset chat</p>
            </div>
            <Link
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-900 hover:bg-slate-100"
              href={`/workspaces/${workspaceId}`}
            >
              ← Back to workspace
            </Link>
          </div>
          <ChatPanel
            activeJobCount={activeJobCount}
            datasetId={datasetId}
            onSubmitted={() => {
              void refresh();
            }}
            workspaceId={workspaceId}
          />
        </div>
      )}
    </WorkspaceShell>
  );
}