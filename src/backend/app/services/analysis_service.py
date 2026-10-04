## Creates runs, finds cached equivalents, queues/retries/cancels jobs.
from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from time import perf_counter
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.db.models.analysis_run import AnalysisRun
from app.db.models.artifact import Artifact
from app.db.models.dataset import Dataset, DatasetVersion
from app.db.models.tool_execution import ToolExecution
from app.eda_tools.registry import TOOL_REGISTRY, list_tools, run_tool
from app.services.cache_service import (
    build_analysis_cache_key,
    get_cached_result,
    set_cached_result,
)
from app.services.dataset_service import get_dataset_overview
from app.services.event_service import publish_analysis_event
from app.services.storage_service import download_bytes

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"
TERMINAL_STATUSES = {STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED}
EXECUTION_MODE_INLINE = "inline"
EXECUTION_MODE_QUEUED = "queued"


class AnalysisValidationError(AppError):
    error_code = "analysis_validation_error"
    default_message = "The analysis request is invalid."


def available_analysis_tools() -> list[dict[str, Any]]:
    return list_tools()


def _now() -> datetime:
    return datetime.now(UTC)


def _error_payload(exc: Exception) -> dict[str, Any]:
    return {
        "type": exc.__class__.__name__,
        "message": str(exc),
    }


def _tool_payload(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for tool in tools:
        name = str(tool["name"]).strip()
        arguments = dict(tool.get("arguments") or {})
        if name not in TOOL_REGISTRY:
            raise AnalysisValidationError(
                "One or more selected tools are not supported.",
                details={"unknown_tool": name},
            )
        normalized.append({"name": name, "arguments": arguments})
    return normalized


def _should_execute_inline(
    *,
    dataset_version: DatasetVersion,
    tools: list[dict[str, Any]],
    include_plots: bool,
) -> bool:
    if include_plots:
        return False
    if len(tools) != 1:
        return False
    if tools[0]["name"] == "relationships":
        return False
    return (
        dataset_version.row_count <= settings.inline_analysis_max_rows
        and dataset_version.column_count <= settings.inline_analysis_max_columns
    )


def _submission_metadata(
    *,
    execution_mode: str,
    queued_at: datetime | None = None,
    celery_task_id: str | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {"execution_mode": execution_mode}
    if queued_at is not None:
        metadata["queued_at"] = queued_at.isoformat()
    if celery_task_id is not None:
        metadata["celery_task_id"] = celery_task_id
    return metadata


def _combined_cache_key(
    *,
    dataset_version_id: UUID,
    tools: list[dict[str, Any]],
) -> str:
    return build_analysis_cache_key(
        str(dataset_version_id),
        "run",
        {"tools": tools},
    )


def _tool_cache_key(
    *,
    dataset_version_id: UUID,
    tool_name: str,
    tool_arguments: dict[str, Any],
) -> str:
    return build_analysis_cache_key(
        str(dataset_version_id),
        tool_name,
        tool_arguments,
    )


def _set_run_progress(
    run: AnalysisRun,
    *,
    status: str,
    stage: str,
    progress_percent: int | None,
) -> None:
    run.status = status
    run.progress_stage = stage
    run.progress_percent = progress_percent


def _publish_run_event(
    run: AnalysisRun,
    *,
    status: str,
    event_type: str | None = None,
    stage: str | None = None,
    progress_percent: int | None = None,
    error: dict[str, Any] | None = None,
) -> None:
    publish_analysis_event(
        workspace_id=run.workspace_id,
        analysis_run_id=run.id,
        status=status,
        event_type=event_type,
        stage=stage,
        progress_percent=progress_percent,
        error=error,
    )


def _dispatch_analysis_run(analysis_run_id: UUID) -> str:
    from app.workers.analysis_tasks import execute_analysis_run_task

    result = execute_analysis_run_task.delay(str(analysis_run_id))
    return str(result.id)


def _read_dataset_frame(dataset_version: DatasetVersion) -> pd.DataFrame:
    content = download_bytes(dataset_version.storage_key)
    return pd.read_csv(BytesIO(content))


def _get_completed_cached_execution(
    *,
    db: Session,
    cache_key: str,
    current_execution_id: UUID,
) -> ToolExecution | None:
    return db.scalar(
        select(ToolExecution)
        .join(ToolExecution.analysis_run)
        .where(
            ToolExecution.cache_key == cache_key,
            ToolExecution.id != current_execution_id,
            ToolExecution.status == STATUS_COMPLETED,
            ToolExecution.result_json.is_not(None),
            AnalysisRun.status == STATUS_COMPLETED,
        )
        .order_by(ToolExecution.completed_at.desc())
    )


def _mark_execution_cached(
    *,
    execution: ToolExecution,
    result: dict[str, Any],
    completed_at: datetime,
    source: str,
    source_execution_id: UUID | None = None,
) -> None:
    execution.status = STATUS_COMPLETED
    execution.result_json = result
    execution.error_json = None
    execution.cache_hit = True
    execution.source_execution_id = source_execution_id
    execution.timings_json = {
        "cache_hit": True,
        "cache_source": source,
    }
    execution.completed_at = completed_at


def _get_analysis_run_for_user(
    *,
    db: Session,
    user_id: UUID,
    analysis_run_id: UUID,
) -> AnalysisRun:
    run = db.scalar(
        select(AnalysisRun)
        .join(AnalysisRun.dataset_version)
        .join(DatasetVersion.dataset)
        .join(Dataset.workspace)
        .options(selectinload(AnalysisRun.tool_executions))
        .where(
            AnalysisRun.id == analysis_run_id,
            Dataset.workspace.has(user_id=user_id),
        )
    )

    if run is None:
        raise NotFoundError("Analysis run was not found.")

    return run


def get_analysis_run(
    *,
    db: Session,
    user_id: UUID,
    analysis_run_id: UUID,
) -> AnalysisRun:
    return _get_analysis_run_for_user(
        db=db,
        user_id=user_id,
        analysis_run_id=analysis_run_id,
    )


def list_analysis_runs_for_dataset(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
) -> list[AnalysisRun]:
    dataset, _dataset_version = get_dataset_overview(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )
    return list(
        db.scalars(
            select(AnalysisRun)
            .join(AnalysisRun.dataset_version)
            .options(selectinload(AnalysisRun.tool_executions))
            .where(DatasetVersion.dataset_id == dataset.id)
            .order_by(AnalysisRun.created_at.desc())
        )
    )


def _artifact_from_payload(
    *,
    payload: dict[str, Any],
    tool_name: str | None,
) -> dict[str, Any]:
    storage_key = payload.get("storage_key") or payload.get("path")
    mime_type = payload.get("mime_type") or payload.get("mime") or "application/octet-stream"
    artifact_type = payload.get("artifact_type") or payload.get("type") or "artifact"
    metadata = {
        key: value
        for key, value in payload.items()
        if key not in {"storage_key", "path", "mime_type", "mime", "artifact_type", "type"}
    }
    return {
        "artifact_type": str(artifact_type),
        "storage_key": str(storage_key) if storage_key is not None else None,
        "mime_type": str(mime_type),
        "tool_name": tool_name,
        "metadata": metadata,
    }


def _extract_artifacts_from_results(run: AnalysisRun) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for execution in run.tool_executions:
        result = execution.result_json or {}
        payloads = result.get("artifacts") or []
        if not isinstance(payloads, list):
            continue
        for payload in payloads:
            if isinstance(payload, dict):
                artifacts.append(
                    _artifact_from_payload(
                        payload=payload,
                        tool_name=execution.tool_name,
                    )
                )
    return artifacts


def list_analysis_artifacts(
    *,
    db: Session,
    user_id: UUID,
    analysis_run_id: UUID,
) -> list[dict[str, Any]]:
    run = get_analysis_run(
        db=db,
        user_id=user_id,
        analysis_run_id=analysis_run_id,
    )
    persisted = list(
        db.scalars(
            select(Artifact).where(Artifact.analysis_run_id == run.id)
        )
    )
    artifacts = [
        {
            "artifact_type": artifact.artifact_type,
            "storage_key": artifact.storage_key,
            "mime_type": artifact.mime_type,
            "tool_name": None,
            "metadata": {"id": str(artifact.id)},
        }
        for artifact in persisted
    ]
    artifacts.extend(_extract_artifacts_from_results(run))
    return artifacts


def get_analysis_results(
    *,
    db: Session,
    user_id: UUID,
    analysis_run_id: UUID,
) -> dict[str, Any]:
    run = get_analysis_run(
        db=db,
        user_id=user_id,
        analysis_run_id=analysis_run_id,
    )
    results = dict(run.results_json or {})
    agent_payload = results.pop("_agent", None)
    explanation = None
    if isinstance(agent_payload, dict):
        interpretation = agent_payload.get("interpretation")
        if isinstance(interpretation, dict):
            explanation = interpretation

    return {
        "run_id": run.id,
        "status": run.status,
        "metrics": results,
        "explanation": explanation,
        "artifacts": list_analysis_artifacts(
            db=db,
            user_id=user_id,
            analysis_run_id=analysis_run_id,
        ),
        "errors": run.error_json,
        "cache_hit": run.cache_hit,
        "source_run_id": run.source_run_id,
    }


def create_analysis_run_record(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
    tools: list[dict[str, Any]],
    include_plots: bool = False,
) -> tuple[AnalysisRun, str]:
    dataset, dataset_version = get_dataset_overview(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )
    selected_tools = _tool_payload(tools)
    request_json = {
        "dataset_id": str(dataset_id),
        "dataset_version_id": str(dataset_version.id),
        "include_plots": include_plots,
        "tools": selected_tools,
    }

    run = AnalysisRun(
        workspace_id=dataset.workspace_id,
        dataset_version_id=dataset_version.id,
        request_json=request_json,
        selected_tools_json=selected_tools,
        status=STATUS_PENDING,
        results_json=None,
        error_json=None,
        timings_json=None,
        cache_key=_combined_cache_key(
            dataset_version_id=dataset_version.id,
            tools=selected_tools,
        ),
        cache_hit=False,
        progress_stage="queued",
        progress_percent=0,
    )
    db.add(run)
    db.flush()

    for selected in selected_tools:
        db.add(
            ToolExecution(
                analysis_run_id=run.id,
                tool_name=selected["name"],
                arguments_json=selected["arguments"],
                status=STATUS_PENDING,
                cache_key=_tool_cache_key(
                    dataset_version_id=dataset_version.id,
                    tool_name=selected["name"],
                    tool_arguments=selected["arguments"],
                ),
                cache_hit=False,
            )
        )

    execution_mode = (
        EXECUTION_MODE_INLINE
        if _should_execute_inline(
            dataset_version=dataset_version,
            tools=selected_tools,
            include_plots=include_plots,
        )
        else EXECUTION_MODE_QUEUED
    )
    run.timings_json = _submission_metadata(execution_mode=execution_mode)
    dataset.workspace.last_activity_at = _now()
    db.commit()
    db.refresh(run)
    _publish_run_event(
        run,
        status=STATUS_PENDING,
        event_type="analysis.queued",
        stage="queued",
        progress_percent=0,
    )

    return get_analysis_run(
        db=db,
        user_id=user_id,
        analysis_run_id=run.id,
    ), execution_mode


def submit_analysis_run(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
    tools: list[dict[str, Any]],
    include_plots: bool = False,
) -> tuple[AnalysisRun, str]:
    run, execution_mode = create_analysis_run_record(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        tools=tools,
        include_plots=include_plots,
    )

    if execution_mode == EXECUTION_MODE_INLINE:
        execute_analysis_run(db=db, analysis_run_id=run.id)
        return (
            get_analysis_run(db=db, user_id=user_id, analysis_run_id=run.id),
            execution_mode,
        )

    try:
        task_id = _dispatch_analysis_run(run.id)
    except Exception as exc:  # noqa: BLE001 - persist dispatch failures on the run.
        run.status = STATUS_FAILED
        run.error_json = {
            "type": exc.__class__.__name__,
            "message": "Analysis run could not be queued.",
            "dispatch_error": str(exc),
        }
        run.progress_stage = "queue dispatch failed"
        run.progress_percent = 100
        run.completed_at = _now()
        db.commit()
        db.refresh(run)
        _publish_run_event(
            run,
            status=STATUS_FAILED,
            event_type="analysis.failed",
            stage=run.progress_stage,
            progress_percent=100,
            error=run.error_json,
        )
    else:
        run.timings_json = _submission_metadata(
            execution_mode=execution_mode,
            queued_at=_now(),
            celery_task_id=task_id,
        )
        db.commit()
        db.refresh(run)
        _publish_run_event(
            run,
            status=STATUS_PENDING,
            event_type="analysis.queued",
            stage="queued",
            progress_percent=0,
        )

    return (
        get_analysis_run(db=db, user_id=user_id, analysis_run_id=run.id),
        execution_mode,
    )


def create_analysis_run(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
    tools: list[dict[str, Any]],
    include_plots: bool = False,
) -> AnalysisRun:
    run, _execution_mode = create_analysis_run_record(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        tools=tools,
        include_plots=include_plots,
    )
    execute_analysis_run(db=db, analysis_run_id=run.id)
    return get_analysis_run(db=db, user_id=user_id, analysis_run_id=run.id)


def execute_analysis_run(
    *,
    db: Session,
    analysis_run_id: UUID,
) -> AnalysisRun:
    run = db.scalar(
        select(AnalysisRun)
        .options(selectinload(AnalysisRun.tool_executions))
        .where(AnalysisRun.id == analysis_run_id)
    )
    if run is None:
        raise NotFoundError("Analysis run was not found.")
    if run.status == STATUS_CANCELLED:
        return run
    if run.status in TERMINAL_STATUSES:
        raise ConflictError("Analysis run has already finished.")

    started = _now()
    _set_run_progress(
        run,
        status=STATUS_RUNNING,
        stage="starting analysis",
        progress_percent=5,
    )
    run.started_at = started
    run.error_json = None
    db.commit()
    _publish_run_event(
        run,
        status=STATUS_RUNNING,
        event_type="analysis.running",
        stage=run.progress_stage,
        progress_percent=run.progress_percent,
    )

    overall_start = perf_counter()
    results: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []

    try:
        frame = _read_dataset_frame(run.dataset_version)
    except Exception as exc:  # noqa: BLE001 - persist dataset read failures on the run.
        now = _now()
        _set_run_progress(
            run,
            status=STATUS_FAILED,
            stage="reading dataset failed",
            progress_percent=100,
        )
        run.error_json = _error_payload(exc)
        run.timings_json = {
            "started_at": started.isoformat(),
            "completed_at": now.isoformat(),
            "duration_ms": round((perf_counter() - overall_start) * 1000, 3),
        }
        run.completed_at = now
        db.commit()
        _publish_run_event(
            run,
            status=STATUS_FAILED,
            event_type="analysis.failed",
            stage=run.progress_stage,
            progress_percent=100,
            error=run.error_json,
        )
        return run

    total_tools = max(len(run.tool_executions), 1)
    cache_hits = 0
    source_run_id: UUID | None = None

    for index, execution in enumerate(run.tool_executions, start=1):
        if run.status == STATUS_CANCELLED:
            break

        execution.status = STATUS_RUNNING
        execution.started_at = _now()
        stage = f"running {execution.tool_name}"
        run.progress_stage = stage
        run.progress_percent = min(95, 10 + int(((index - 1) / total_tools) * 80))
        db.commit()
        _publish_run_event(
            run,
            status=STATUS_RUNNING,
            event_type="analysis.progress",
            stage=stage,
            progress_percent=run.progress_percent,
        )

        if execution.cache_key is None:
            execution.cache_key = _tool_cache_key(
                dataset_version_id=run.dataset_version_id,
                tool_name=execution.tool_name,
                tool_arguments=execution.arguments_json,
            )

        cached_result = get_cached_result(execution.cache_key)
        if cached_result is not None:
            completed = _now()
            _mark_execution_cached(
                execution=execution,
                result=cached_result,
                completed_at=completed,
                source="redis",
            )
            results[execution.tool_name] = cached_result
            cache_hits += 1
            db.commit()
            continue

        cached_execution = _get_completed_cached_execution(
            db=db,
            cache_key=execution.cache_key,
            current_execution_id=execution.id,
        )
        if cached_execution is not None and cached_execution.result_json is not None:
            completed = _now()
            _mark_execution_cached(
                execution=execution,
                result=cached_execution.result_json,
                completed_at=completed,
                source="postgres",
                source_execution_id=cached_execution.id,
            )
            results[execution.tool_name] = cached_execution.result_json
            cache_hits += 1
            source_run_id = cached_execution.analysis_run_id
            set_cached_result(execution.cache_key, cached_execution.result_json)
            db.commit()
            continue

        tool_start = perf_counter()
        try:
            result = run_tool(
                execution.tool_name,
                frame,
                **execution.arguments_json,
            )
        except Exception as exc:  # noqa: BLE001 - one tool failure should not hide run state.
            completed = _now()
            execution.status = STATUS_FAILED
            execution.error_json = _error_payload(exc)
            execution.timings_json = {
                "duration_ms": round((perf_counter() - tool_start) * 1000, 3),
            }
            execution.completed_at = completed
            errors.append(
                {
                    "tool": execution.tool_name,
                    "error": execution.error_json,
                }
            )
        else:
            completed = _now()
            execution.status = STATUS_COMPLETED
            execution.result_json = result
            execution.error_json = None
            execution.timings_json = {
                "duration_ms": round((perf_counter() - tool_start) * 1000, 3),
            }
            execution.completed_at = completed
            results[execution.tool_name] = result
            set_cached_result(execution.cache_key, result)

        db.commit()

    completed = _now()
    run.results_json = results
    run.error_json = {"tools": errors} if errors else None
    final_status = STATUS_FAILED if errors else STATUS_COMPLETED
    _set_run_progress(
        run,
        status=final_status,
        stage="failed" if errors else "completed",
        progress_percent=100,
    )
    run.cache_hit = cache_hits == len(run.tool_executions) and not errors
    run.source_run_id = source_run_id if run.cache_hit else None
    run.completed_at = completed
    run.timings_json = {
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "duration_ms": round((perf_counter() - overall_start) * 1000, 3),
        "cache_hits": cache_hits,
    }
    db.commit()
    db.refresh(run)
    _publish_run_event(
        run,
        status=run.status,
        event_type="analysis.failed" if errors else "analysis.completed",
        stage=run.progress_stage,
        progress_percent=100,
        error=run.error_json,
    )
    return run


def retry_analysis_run(
    *,
    db: Session,
    user_id: UUID,
    analysis_run_id: UUID,
) -> AnalysisRun:
    run = _get_analysis_run_for_user(
        db=db,
        user_id=user_id,
        analysis_run_id=analysis_run_id,
    )
    if run.status not in TERMINAL_STATUSES:
        raise ConflictError("Only finished analysis runs can be retried.")

    run.status = STATUS_PENDING
    run.started_at = None
    run.completed_at = None
    run.results_json = None
    run.error_json = None
    run.timings_json = None
    run.cache_hit = False
    run.source_run_id = None
    run.progress_stage = "queued"
    run.progress_percent = 0
    for execution in run.tool_executions:
        execution.status = STATUS_PENDING
        execution.started_at = None
        execution.completed_at = None
        execution.result_json = None
        execution.error_json = None
        execution.timings_json = None
        execution.cache_hit = False
        execution.source_execution_id = None
    db.commit()

    execute_analysis_run(db=db, analysis_run_id=run.id)
    return get_analysis_run(
        db=db,
        user_id=user_id,
        analysis_run_id=analysis_run_id,
    )


def cancel_analysis_run(
    *,
    db: Session,
    user_id: UUID,
    analysis_run_id: UUID,
) -> AnalysisRun:
    run = _get_analysis_run_for_user(
        db=db,
        user_id=user_id,
        analysis_run_id=analysis_run_id,
    )
    if run.status in TERMINAL_STATUSES:
        raise ConflictError("Analysis run has already finished.")

    now = _now()
    run.status = STATUS_CANCELLED
    run.completed_at = now
    run.error_json = None
    run.progress_stage = "cancelled"
    run.progress_percent = 100
    for execution in run.tool_executions:
        if execution.status in {STATUS_PENDING, STATUS_RUNNING}:
            execution.status = STATUS_CANCELLED
            execution.completed_at = now
    db.commit()
    db.refresh(run)
    _publish_run_event(
        run,
        status=STATUS_CANCELLED,
        event_type="analysis.cancelled",
        stage=run.progress_stage,
        progress_percent=100,
    )
    return run
