"use client";

import { use, useCallback, useEffect } from "react";
import { RunDetail } from "@/components/analysis/run-detail";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Spinner } from "@/components/ui/spinner";
import { useAnalysisRunDetail } from "@/hooks/use-analysis-runs";
import { useWorkspaceEvents } from "@/hooks/use-workspace-events";
import { isActiveRunStatus } from "@/types/analysis";

export default function AnalysisRunDetailPage({
  params,
}: {
  params: Promise<{ workspaceId: string; runId: string }>;
}) {
  const { workspaceId, runId } = use(params);
  const { run, isLoading, error, refresh } = useAnalysisRunDetail(runId);
  const handleEvent = useCallback(() => {
    void refresh();
  }, [refresh]);
  useWorkspaceEvents(workspaceId, handleEvent);

  useEffect(() => {
    if (!run || !isActiveRunStatus(run.status)) {
      return;
    }
    const timer = window.setInterval(() => {
      void refresh();
    }, 2500);
    return () => window.clearInterval(timer);
  }, [run, refresh]);

  return (
    <WorkspaceShell>
      {isLoading && !run ? (
        <div className="p-8">
          <Spinner label="Loading analysis run..." />
        </div>
      ) : error || !run ? (
        <div className="p-6 text-sm text-red-600">
          {error ?? "Analysis run not found."}
        </div>
      ) : (
        <RunDetail
          onChanged={() => {
            void refresh();
          }}
          run={run}
          workspaceId={workspaceId}
        />
      )}
    </WorkspaceShell>
  );
}
