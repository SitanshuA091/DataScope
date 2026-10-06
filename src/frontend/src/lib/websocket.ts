import { WS_BASE_URL } from "./constants";
import type { WorkspaceEvent } from "@/types/analysis";

export function connectWorkspaceEvents(
  workspaceId: string,
  onEvent: (event: WorkspaceEvent) => void,
  onStatusChange?: (status: "connected" | "disconnected") => void,
) {
  let closed = false;
  let socket: WebSocket | null = null;
  let retryId: number | null = null;

  const connect = () => {
    socket = new WebSocket(`${WS_BASE_URL}/api/v1/ws/workspaces/${workspaceId}`);

    socket.addEventListener("open", () => onStatusChange?.("connected"));
    socket.addEventListener("message", (message) => {
      try {
        onEvent(JSON.parse(message.data) as WorkspaceEvent);
      } catch {
        onEvent({ type: "unparseable", raw: message.data });
      }
    });
    socket.addEventListener("close", () => {
      onStatusChange?.("disconnected");
      if (!closed) {
        retryId = window.setTimeout(connect, 2000);
      }
    });
  };

  connect();

  return () => {
    closed = true;
    if (retryId !== null) {
      window.clearTimeout(retryId);
    }
    socket?.close();
  };
}
