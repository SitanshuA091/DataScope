"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import type { AnalysisTool, AnalysisToolListResponse } from "@/types/analysis";

export function useAnalysisTools() {
  const [tools, setTools] = useState<AnalysisTool[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiFetch<AnalysisToolListResponse>(
        "/analysis/tools",
      );
      setTools(response.tools);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load analysis tools.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(refresh);
  }, [refresh]);

  return { tools, isLoading, error, refresh };
}
