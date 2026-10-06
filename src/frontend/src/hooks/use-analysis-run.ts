"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { USE_MOCKS } from "@/lib/constants";
import type { AnalysisRunSubmission, ToolSelection } from "@/types/analysis";

export function useAnalysisRun(datasetId: string | null | undefined) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitAnalysis(tools: ToolSelection[], includePlots = true) {
    if (!datasetId) {
      throw new Error("A dataset is required before running analysis.");
    }

    setIsSubmitting(true);
    setError(null);

    try {
      if (USE_MOCKS) {
        await new Promise((resolve) => window.setTimeout(resolve, 450));
        return {
          id: `mock-run-${Date.now()}`,
          status: "pending",
          execution_mode: "queued",
          dataset_version_id: "version-sales-q4",
          created_at: new Date().toISOString(),
        } satisfies AnalysisRunSubmission;
      }

      return await apiFetch<AnalysisRunSubmission>(
        `/datasets/${datasetId}/analysis-runs`,
        {
          method: "POST",
          body: {
            tools,
            include_plots: includePlots,
          },
        },
      );
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Unable to submit analysis.";
      setError(message);
      throw requestError;
    } finally {
      setIsSubmitting(false);
    }
  }

  return { submitAnalysis, isSubmitting, error };
}
