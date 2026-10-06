"use client";

import { useEffect, useState } from "react";
import { USE_MOCKS } from "@/lib/constants";
import { connectWorkspaceEvents } from "@/lib/websocket";
import type { WorkspaceEvent } from "@/types/analysis";

export function useWorkspaceEvents(
  workspaceId: string,
  onEvent: (event: WorkspaceEvent) => void,
) {
  const [status, setStatus] = useState<"connected" | "disconnected">(
    USE_MOCKS ? "connected" : "disconnected",
  );

  useEffect(() => {
    if (USE_MOCKS) {
      return;
    }

    return connectWorkspaceEvents(workspaceId, onEvent, setStatus);
  }, [workspaceId, onEvent]);

  return status;
}
