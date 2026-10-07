"use client";

import { useEffect, useState } from "react";
import { connectWorkspaceEvents } from "@/lib/websocket";
import type { WorkspaceEvent } from "@/types/analysis";

export function useWorkspaceEvents(
  workspaceId: string,
  onEvent: (event: WorkspaceEvent) => void,
) {
  const [status, setStatus] = useState<"connected" | "disconnected">(
    "disconnected",
  );

  useEffect(() => {
    return connectWorkspaceEvents(workspaceId, onEvent, setStatus);
  }, [workspaceId, onEvent]);

  return status;
}
