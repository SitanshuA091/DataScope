"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAnalysisRun } from "@/hooks/use-analysis-run";
import type { ToolSelection } from "@/types/analysis";

type ToolOption = {
  id: string;
  label: string;
  detail: string;
  arguments?: Record<string, unknown>;
};

const toolOptions: ToolOption[] = [
  {
    id: "schema_profile",
    label: "Schema profile",
    detail: "Column types, nullability, row and column readiness.",
  },
  {
    id: "missingness_report",
    label: "Missingness report",
    detail: "Missing values by column and possible remediation targets.",
  },
  {
    id: "outlier_scan",
    label: "Outlier scan",
    detail: "Numeric outliers and records that may distort analysis.",
  },
  {
    id: "correlation_scan",
    label: "Correlation scan",
    detail: "Pairwise numeric relationships and strong associations.",
  },
  {
    id: "segment_summary",
    label: "Segment summary",
    detail: "Grouped metrics for category columns such as region or stage.",
    arguments: { group_by: "region" },
  },
];

export function DeterministicToolPanel({
  datasetId,
  onSubmitted,
}: {
  datasetId: string | null;
  onSubmitted: () => void;
}) {
  const [selectedTools, setSelectedTools] = useState<Set<string>>(
    () => new Set(["schema_profile", "missingness_report"]),
  );
  const [includePlots, setIncludePlots] = useState(true);
  const [question, setQuestion] = useState(
    "Prepare this dataset for analysis and flag quality risks.",
  );
  const { submitAnalysis, isSubmitting, error } = useAnalysisRun(datasetId);

  const tools = useMemo<ToolSelection[]>(
    () =>
      toolOptions
        .filter((tool) => selectedTools.has(tool.id))
        .map((tool) => ({
          name: tool.id,
          arguments: {
            ...tool.arguments,
            question: question.trim(),
          },
        })),
    [question, selectedTools],
  );

  function toggleTool(toolId: string) {
    setSelectedTools((current) => {
      const next = new Set(current);
      if (next.has(toolId)) {
        next.delete(toolId);
      } else {
        next.add(toolId);
      }
      return next;
    });
  }

  async function runTools() {
    if (!datasetId || tools.length === 0) {
      return;
    }

    await submitAnalysis(tools, includePlots);
    onSubmitted();
  }

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 px-5 py-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-950">
              Deterministic tools
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Run repeatable checks before asking for interpretation.
            </p>
          </div>
          <label className="inline-flex items-center gap-2 text-sm text-slate-700">
            <input
              checked={includePlots}
              className="h-4 w-4 rounded border-slate-300"
              onChange={(event) => setIncludePlots(event.target.checked)}
              type="checkbox"
            />
            Include plots
          </label>
        </div>
      </div>

      <div className="grid gap-0 divide-y divide-slate-100 lg:grid-cols-5 lg:divide-x lg:divide-y-0">
        {toolOptions.map((tool) => (
          <label
            className="flex min-h-32 cursor-pointer flex-col gap-3 p-4 transition hover:bg-slate-50"
            key={tool.id}
          >
            <span className="flex items-start gap-3">
              <input
                checked={selectedTools.has(tool.id)}
                className="mt-1 h-4 w-4 rounded border-slate-300"
                onChange={() => toggleTool(tool.id)}
                type="checkbox"
              />
              <span>
                <span className="block text-sm font-semibold text-slate-950">
                  {tool.label}
                </span>
                <span className="mt-1 block text-xs leading-5 text-slate-600">
                  {tool.detail}
                </span>
              </span>
            </span>
          </label>
        ))}
      </div>

      <div className="border-t border-slate-200 bg-slate-50 px-5 py-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
          <input
            className="min-h-10 flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950"
            onChange={(event) => setQuestion(event.target.value)}
            value={question}
          />
          <Button
            className="xl:w-44"
            disabled={!datasetId || selectedTools.size === 0 || isSubmitting}
            onClick={runTools}
          >
            {isSubmitting ? "Queueing..." : "Run tools"}
          </Button>
        </div>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </div>
    </Card>
  );
}
