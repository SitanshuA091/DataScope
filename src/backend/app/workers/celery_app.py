"""Celery configuration for background analysis execution."""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "datalens_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.analysis_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    worker_concurrency=settings.celery_worker_concurrency,
    task_soft_time_limit=settings.celery_task_soft_time_limit_seconds,
    task_time_limit=settings.celery_task_time_limit_seconds,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
