"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import type {
  AnalysisRun,
  AnalysisRunSubmission,
  ToolSelection,
} from "@/types/analysis";

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

export function useAnalysisRunActions() {
  const [isMutating, setIsMutating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function retryRun(runId: string) {
    setIsMutating(true);
    setError(null);

    try {
      return await apiFetch<AnalysisRun>(`/analysis-runs/${runId}/retry`, {
        method: "POST",
      });
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Retry failed.";
      setError(message);
      throw requestError;
    } finally {
      setIsMutating(false);
    }
  }

  async function cancelRun(runId: string) {
    setIsMutating(true);
    setError(null);

    try {
      return await apiFetch<AnalysisRun>(`/analysis-runs/${runId}/cancel`, {
        method: "POST",
      });
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Cancel failed.";
      setError(message);
      throw requestError;
    } finally {
      setIsMutating(false);
    }
  }

  return { retryRun, cancelRun, isMutating, error };
}
