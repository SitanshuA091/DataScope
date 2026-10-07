"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAnalysisRun } from "@/hooks/use-analysis-run";
import { useAnalysisTools } from "@/hooks/use-analysis-tools";
import type { ToolSelection } from "@/types/analysis";

function formatToolName(name: string) {
  return name.replaceAll("_", " ");
}

export function DeterministicToolPanel({
  datasetId,
  onSubmitted,
}: {
  datasetId: string | null;
  onSubmitted: () => void;
}) {
  const [selectedTools, setSelectedTools] = useState<Set<string>>(
    () => new Set(["high_level", "quality"]),
  );
  const [includePlots, setIncludePlots] = useState(true);
  const [question, setQuestion] = useState(
    "Prepare this dataset for analysis and flag quality risks.",
  );
  const { submitAnalysis, isSubmitting, error } = useAnalysisRun(datasetId);
  const {
    tools: availableTools,
    isLoading: isLoadingTools,
    error: toolsError,
  } = useAnalysisTools();

  const tools = useMemo<ToolSelection[]>(
    () =>
      availableTools
        .filter((tool) => selectedTools.has(tool.name))
        .map((tool) => ({
          name: tool.name,
          arguments: {
            question: question.trim(),
          },
        })),
    [availableTools, question, selectedTools],
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

      <div className="grid gap-0 divide-y divide-slate-100 lg:grid-cols-4 lg:divide-x lg:divide-y-0">
        {isLoadingTools ? (
          <p className="p-5 text-sm text-slate-600 lg:col-span-4">
            Loading backend tool registry...
          </p>
        ) : null}
        {toolsError ? (
          <p className="p-5 text-sm text-red-600 lg:col-span-4">
            {toolsError}
          </p>
        ) : null}
        {!isLoadingTools && !toolsError && availableTools.length === 0 ? (
          <p className="p-5 text-sm text-slate-600 lg:col-span-4">
            No analysis tools are available from the backend.
          </p>
        ) : null}
        {availableTools.map((tool) => (
          <label
            className="flex min-h-32 cursor-pointer flex-col gap-3 p-4 transition hover:bg-slate-50"
            key={tool.name}
          >
            <span className="flex items-start gap-3">
              <input
                checked={selectedTools.has(tool.name)}
                className="mt-1 h-4 w-4 rounded border-slate-300"
                onChange={() => toggleTool(tool.name)}
                type="checkbox"
              />
              <span>
                <span className="block text-sm font-semibold text-slate-950">
                  {formatToolName(tool.name)}
                </span>
                <span className="mt-1 block text-xs leading-5 text-slate-600">
                  {tool.description}
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
