## Redis cache keys and cached tool/result retrieval.
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )


def build_analysis_cache_key(
    dataset_version_id: str,
    tool_name: str,
    tool_arguments: dict[str, Any],
    tool_version: str = "v1",
) -> str:
    normalized_arguments = json.dumps(
        tool_arguments,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    raw_key = (
        f"{dataset_version_id}:"
        f"{tool_name}:"
        f"{tool_version}:"
        f"{normalized_arguments}"
    )

    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return f"analysis:{digest}"


def get_cached_result(cache_key: str) -> dict[str, Any] | None:
    try:
        value = get_redis_client().get(cache_key)
    except RedisError:
        return None

    if value is None:
        return None

    return json.loads(value)


def set_cached_result(
    cache_key: str,
    result: dict[str, Any],
) -> None:
    try:
        get_redis_client().setex(
            cache_key,
            settings.cache_ttl_seconds,
            json.dumps(result, default=str),
        )
    except RedisError:
        # Redis cache failure must never fail a completed analysis.
        return


def delete_cached_result(cache_key: str) -> None:
    try:
        get_redis_client().delete(cache_key)
    except RedisError:
        return