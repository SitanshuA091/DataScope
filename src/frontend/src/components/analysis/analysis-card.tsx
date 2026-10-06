import { Card } from "@/components/ui/card";
import { formatDateTime } from "@/lib/formatters";
import type { AnalysisRun } from "@/types/analysis";
import { ResultMetrics } from "./result-metrics";
import { RetryAnalysisButton } from "./retry-analysis-button";
import { RunStatus } from "./run-status";

export function AnalysisCard({ run }: { run: AnalysisRun }) {
  return (
    <Card className="p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-950">
            Analysis run
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Created {formatDateTime(run.created_at)}
          </p>
        </div>
        <RunStatus progress={run.progress_percent} status={run.status} />
      </div>
      <div className="mt-4">
        <ResultMetrics results={run.results_json} />
      </div>
      {run.error_json ? (
        <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {JSON.stringify(run.error_json)}
        </p>
      ) : null}
      <div className="mt-4 flex justify-end">
        <RetryAnalysisButton />
      </div>
    </Card>
  );
}
