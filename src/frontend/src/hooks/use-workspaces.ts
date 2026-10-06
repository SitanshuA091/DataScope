"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { USE_MOCKS } from "@/lib/constants";
import { getMockWorkspaceDetail, mockWorkspaces } from "@/lib/mock-data";
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
    if (USE_MOCKS) {
      setWorkspaces(mockWorkspaces);
      setError(null);
      setIsLoading(false);
      return;
    }

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
      if (USE_MOCKS) {
        const timestamp = new Date().toISOString();
        return {
          id: "demo-sales",
          user_id: "local-user",
          title: title?.trim() || "Untitled workspace",
          last_activity_at: timestamp,
          deleted_at: null,
          scheduled_deletion_at: null,
          created_at: timestamp,
          updated_at: timestamp,
        };
      }

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
    if (USE_MOCKS) {
      setDetail(getMockWorkspaceDetail(workspaceId));
      setError(null);
      setIsLoading(false);
      return;
    }

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
