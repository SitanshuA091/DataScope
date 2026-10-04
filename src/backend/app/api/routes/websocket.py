## Authenticated workspace/run WebSocket connections.
from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.db.models.workspace import Workspace
from app.db.session import SessionLocal
from app.services.event_service import iter_workspace_events

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/workspaces/{workspace_id}")
async def workspace_events(
    websocket: WebSocket,
    workspace_id: UUID,
) -> None:
    user_id = websocket.session.get("user_id")
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    db = SessionLocal()
    try:
        workspace = db.get(Workspace, workspace_id)
        if workspace is None or str(workspace.user_id) != str(user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        db.close()

    await websocket.accept()
    events = iter_workspace_events(workspace_id)

    try:
        while True:
            event = await asyncio.to_thread(next, events)
            await websocket.send_json(event)
    except (StopIteration, WebSocketDisconnect):
        return
