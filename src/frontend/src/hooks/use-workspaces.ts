"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import type {
  Workspace,
  WorkspaceDetail,
  WorkspaceListResponse,
} from "@/types/workspace";

export function useWorkspaces() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiFetch<WorkspaceListResponse>("/workspaces");
      setWorkspaces(response.workspaces);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load workspaces.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(refresh);
  }, [refresh]);

  const createWorkspace = useCallback(
    async (title?: string | null) => {
      const workspace = await apiFetch<Workspace>("/workspaces", {
        method: "POST",
        body: { title: title?.trim() || null },
      });
      await refresh();
      return workspace;
    },
    [refresh],
  );

  return { workspaces, isLoading, error, refresh, createWorkspace };
}

export function useWorkspaceDetail(workspaceId: string) {
  const [detail, setDetail] = useState<WorkspaceDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      setDetail(await apiFetch<WorkspaceDetail>(`/workspaces/${workspaceId}`));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load this workspace.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    void Promise.resolve().then(refresh);
  }, [refresh]);

  return { detail, isLoading, error, refresh, setDetail };
}
