"""Celery tasks for persisted analysis runs."""
from __future__ import annotations

from uuid import UUID

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.analysis_service import execute_analysis_run
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=settings.celery_retry_max_attempts,
    name="app.workers.analysis_tasks.execute_analysis_run_task",
)
def execute_analysis_run_task(self, analysis_run_id: str) -> str:
    del self
    db = SessionLocal()
    try:
        execute_analysis_run(
            db=db,
            analysis_run_id=UUID(analysis_run_id),
        )
    finally:
        db.close()

    return analysis_run_id
