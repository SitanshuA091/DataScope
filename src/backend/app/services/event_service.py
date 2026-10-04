## Publishes worker progress events for WebSocket clients.
from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any
from uuid import UUID

from redis.exceptions import RedisError

from app.services.cache_service import get_redis_client


def workspace_channel(workspace_id: UUID) -> str:
    return f"workspace:{workspace_id}:events"


def publish_workspace_event(
    *,
    workspace_id: UUID,
    event: dict[str, Any],
) -> None:
    try:
        get_redis_client().publish(
            workspace_channel(workspace_id),
            json.dumps(event, default=str),
        )
    except RedisError:
        return


def publish_analysis_event(
    *,
    workspace_id: UUID,
    analysis_run_id: UUID,
    status: str,
    event_type: str | None = None,
    stage: str | None = None,
    progress_percent: int | None = None,
    error: dict[str, Any] | None = None,
) -> None:
    event: dict[str, Any] = {
        "type": event_type or f"analysis.{status}",
        "run_id": str(analysis_run_id),
        "status": status,
    }
    if stage is not None:
        event["stage"] = stage
    if progress_percent is not None:
        event["progress_percent"] = progress_percent
    if error is not None:
        event["error"] = error

    publish_workspace_event(workspace_id=workspace_id, event=event)


def iter_workspace_events(workspace_id: UUID) -> Iterator[dict[str, Any]]:
    pubsub = get_redis_client().pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(workspace_channel(workspace_id))
    try:
        while True:
            message = pubsub.get_message(timeout=1.0)
            if not message:
                continue
            data = message.get("data")
            if not data:
                continue
            yield json.loads(str(data))
    finally:
        pubsub.close()
