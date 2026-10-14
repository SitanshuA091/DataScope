"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import {
  isTerminalRunStatus,
  type ArtifactListResponse,
  type RunResults,
} from "@/types/analysis";

export function useRunResults(
  runId: string | null | undefined,
  status?: string | null,
) {
  const [results, setResults] = useState<RunResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const enabled = Boolean(runId && isTerminalRunStatus(status));

  const refresh = useCallback(async () => {
    if (!runId || !isTerminalRunStatus(status)) {
      setResults(null);
      setError(null);
      setIsLoading(false);
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload = await apiFetch<RunResults>(
        `/analysis-runs/${runId}/results`,
      );
      setResults(payload);
      return payload;
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Unable to load analysis results.";
      setError(message);
      throw requestError;
    } finally {
      setIsLoading(false);
    }
  }, [runId, status]);

  useEffect(() => {
    void Promise.resolve().then(() => refresh().catch(() => undefined));
  }, [enabled, refresh]);

  return { results, isLoading, error, refresh, enabled };
}

export function useRunArtifacts(
  runId: string | null | undefined,
  status?: string | null,
) {
  const [artifacts, setArtifacts] = useState<ArtifactListResponse["artifacts"]>(
    [],
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const enabled = Boolean(runId && isTerminalRunStatus(status));

  const refresh = useCallback(async () => {
    if (!runId || !isTerminalRunStatus(status)) {
      setArtifacts([]);
      setError(null);
      setIsLoading(false);
      return [];
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload = await apiFetch<ArtifactListResponse>(
        `/analysis-runs/${runId}/artifacts`,
      );
      setArtifacts(payload.artifacts);
      return payload.artifacts;
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Unable to load artifacts.";
      setError(message);
      throw requestError;
    } finally {
      setIsLoading(false);
    }
  }, [runId, status]);

  useEffect(() => {
    void Promise.resolve().then(() => refresh().catch(() => undefined));
  }, [enabled, refresh]);

  return { artifacts, isLoading, error, refresh, enabled };
}
