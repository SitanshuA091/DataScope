"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import type {
  AnalysisRun,
  AnalysisRunHistoryItem,
  AnalysisRunHistoryResponse,
} from "@/types/analysis";

export function useAnalysisRuns(datasetId: string | null | undefined) {
  const [runs, setRuns] = useState<AnalysisRunHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!datasetId) {
      setRuns([]);
      setError(null);
      setIsLoading(false);
      return [];
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiFetch<AnalysisRunHistoryResponse>(
        `/datasets/${datasetId}/analysis-runs`,
      );
      setRuns(response.analysis_runs);
      return response.analysis_runs;
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load analysis runs.",
      );
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    void Promise.resolve().then(refresh);
  }, [refresh]);

  return { runs, isLoading, error, refresh };
}

export function useAnalysisRunDetail(runId: string | null | undefined) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(runId));
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!runId) {
      setRun(null);
      setError(null);
      setIsLoading(false);
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload = await apiFetch<AnalysisRun>(`/analysis-runs/${runId}`);
      setRun(payload);
      return payload;
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load this analysis run.",
      );
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    void Promise.resolve().then(refresh);
  }, [refresh]);

  return { run, isLoading, error, refresh, setRun };
}
