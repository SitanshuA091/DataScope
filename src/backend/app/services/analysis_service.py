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

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.db.models.analysis_run import AnalysisRun
from app.db.models.dataset import Dataset, DatasetVersion
from app.db.models.tool_execution import ToolExecution
from app.eda_tools.registry import TOOL_REGISTRY, list_tools, run_tool
from app.services.dataset_service import get_dataset_overview
from app.services.storage_service import download_bytes

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"
TERMINAL_STATUSES = {STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED}


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


def _read_dataset_frame(dataset_version: DatasetVersion) -> pd.DataFrame:
    content = download_bytes(dataset_version.storage_key)
    return pd.read_csv(BytesIO(content))


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


def create_analysis_run(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
    tools: list[dict[str, Any]],
    include_plots: bool = False,
) -> AnalysisRun:
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
            )
        )

    dataset.workspace.last_activity_at = _now()
    db.commit()
    db.refresh(run)

    execute_analysis_run(
        db=db,
        analysis_run_id=run.id,
    )
    return get_analysis_run(
        db=db,
        user_id=user_id,
        analysis_run_id=run.id,
    )


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
    run.status = STATUS_RUNNING
    run.started_at = started
    run.error_json = None
    db.commit()

    overall_start = perf_counter()
    results: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []

    try:
        frame = _read_dataset_frame(run.dataset_version)
    except Exception as exc:
        now = _now()
        run.status = STATUS_FAILED
        run.error_json = _error_payload(exc)
        run.timings_json = {
            "started_at": started.isoformat(),
            "completed_at": now.isoformat(),
            "duration_ms": round((perf_counter() - overall_start) * 1000, 3),
        }
        run.completed_at = now
        db.commit()
        return run

    for execution in run.tool_executions:
        if run.status == STATUS_CANCELLED:
            break

        execution.status = STATUS_RUNNING
        execution.started_at = _now()
        db.commit()

        tool_start = perf_counter()
        try:
            result = run_tool(
                execution.tool_name,
                frame,
                **execution.arguments_json,
            )
        except Exception as exc:
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

        db.commit()

    completed = _now()
    run.results_json = results
    run.error_json = {"tools": errors} if errors else None
    run.status = STATUS_FAILED if errors else STATUS_COMPLETED
    run.completed_at = completed
    run.timings_json = {
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "duration_ms": round((perf_counter() - overall_start) * 1000, 3),
    }
    db.commit()
    db.refresh(run)
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
    for execution in run.tool_executions:
        execution.status = STATUS_PENDING
        execution.started_at = None
        execution.completed_at = None
        execution.result_json = None
        execution.error_json = None
        execution.timings_json = None
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
    for execution in run.tool_executions:
        if execution.status in {STATUS_PENDING, STATUS_RUNNING}:
            execution.status = STATUS_CANCELLED
            execution.completed_at = now
    db.commit()
    db.refresh(run)
    return run
