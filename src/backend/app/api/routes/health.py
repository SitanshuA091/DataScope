## Health/readiness endpoints for API, DB, and Redis
from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine
from app.services.cache_service import get_redis_client


router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready")
def readiness_check(response: Response) -> dict[str, object]:
    checks: dict[str, str] = {}

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except SQLAlchemyError:
        checks["postgres"] = "unavailable"

    try:
        get_redis_client().ping()
        checks["redis"] = "ok"
    except RedisError:
        checks["redis"] = "unavailable"

    is_ready = all(value == "ok" for value in checks.values())

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }