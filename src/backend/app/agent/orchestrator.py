"""Dataset-agent orchestration flow.

Coordinates context retrieval, tool planning, analysis execution, grounded
interpretation, and optional conversation persistence.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.agent.contracts import (
    AgentRunResult,
    AnalysisInterpretation,
    ConversationTurn,
    DatasetColumn,
    DatasetContext,
)
from app.agent.interpreter import AgentInterpreter
from app.agent.planner import AgentPlanner
from app.db.models.analysis_run import AnalysisRun
from app.services.cache_service import get_cached_result, set_cached_result
from app.services.storage_service import download_bytes
from app.services.analysis_service import (
    build_analysis_cache_key,
    create_analysis_run,
)
from app.services.context_service import save_message
from app.services.dataset_service import get_dataset_overview


def _parse_dataset_file(
    dataset_version: Any,
    *,
    selected_columns: list[str] | None = None,
    max_sample_rows: int = 30,
) -> dict[str, Any]:
    content = download_bytes(dataset_version.storage_key)
    frame = pd.read_csv(BytesIO(content))
    total_rows = int(dataset_version.row_count or len(frame))
    total_cols = int(dataset_version.column_count or len(frame.columns))

    cols = list(frame.columns)
    if selected_columns:
        valid_cols = [c for c in selected_columns if c in frame.columns]
        if valid_cols:
            cols = valid_cols

    sub_frame = frame[cols]

    schema_info = []
    for col in cols:
        s = frame[col]
        non_null = int(s.count())
        null_count = total_rows - non_null
        col_summary: dict[str, Any] = {
            "name": col,
            "dtype": str(s.dtype),
            "non_null_count": non_null,
            "null_count": null_count,
        }
        if pd.api.types.is_numeric_dtype(s):
            clean = s.dropna()
            col_summary["min"] = None if clean.empty else float(clean.min())
            col_summary["max"] = None if clean.empty else float(clean.max())
            col_summary["mean"] = (
                None if clean.empty else round(float(clean.mean()), 3)
            )
        else:
            col_summary["unique_count"] = int(s.nunique(dropna=True))
            top_vals = s.value_counts().head(5).to_dict()
            col_summary["top_values"] = {str(k): int(v) for k, v in top_vals.items()}
        schema_info.append(col_summary)

    sample_rows = sub_frame.head(max_sample_rows).to_dict(orient="records")

    return {
        "filename": getattr(dataset_version, "original_filename", "dataset.csv"),
        "row_count": total_rows,
        "column_count": total_cols,
        "selected_columns": cols,
        "schema": schema_info,
        "sample_rows": sample_rows,
        "sample_row_count": len(sample_rows),
    }


def _dataset_context(
    *,
    dataset_id: UUID,
    dataset_version: Any,
    active_columns: list[str] | None = None,
) -> DatasetContext:
    return DatasetContext(
        dataset_id=dataset_id,
        dataset_version_id=dataset_version.id,
        row_count=dataset_version.row_count,
        column_count=dataset_version.column_count,
        columns=[
            DatasetColumn.model_validate(column)
            for column in dataset_version.schema_json
        ],
        active_columns=active_columns or [],
    )


def _assistant_text_from_interpretation(answer: str, findings: list[str]) -> str:
    if not findings:
        return answer
    return "\n".join([answer, "", "Key findings:", *[f"- {item}" for item in findings]])


class AnalysisAgentOrchestrator:
    def __init__(
        self,
        *,
        planner: AgentPlanner | None = None,
        interpreter: AgentInterpreter | None = None,
    ) -> None:
        self.planner = planner or AgentPlanner()
        self.interpreter = interpreter or AgentInterpreter()

    def run(
        self,
        *,
        db: Session,
        user_id: UUID,
        dataset_id: UUID,
        question: str,
        active_columns: list[str] | None = None,
        history: list[ConversationTurn] | None = None,
        persist_messages: bool = True,
    ) -> AgentRunResult:
        dataset, dataset_version = get_dataset_overview(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
        )
        context = _dataset_context(
            dataset_id=dataset.id,
            dataset_version=dataset_version,
            active_columns=active_columns,
        )

        plan = self.planner.plan(
            question=question,
            dataset_context=context,
            history=history,
        )

        user_message_record = None
        if persist_messages:
            user_message_record = save_message(
                db=db,
                user_id=user_id,
                dataset_id=dataset_id,
                role="user",
                content=question,
            )

        if plan.requires_clarification:
            assistant_message = plan.clarification_question or "Can you clarify?"
            clarification_record = None
            if persist_messages:
                clarification_record = save_message(
                    db=db,
                    user_id=user_id,
                    dataset_id=dataset_id,
                    role="assistant",
                    content=assistant_message,
                )
            return AgentRunResult(
                dataset_id=dataset.id,
                dataset_version_id=dataset_version.id,
                question=question,
                plan=plan,
                assistant_message=assistant_message,
                user_message_id=user_message_record.id if user_message_record else None,
                assistant_message_id=clarification_record.id if clarification_record else None,
            )

        eda_tools = [tool for tool in plan.tools if tool.name != "file_qa"]

        if not eda_tools:
            # Direct file Q&A via LLM client without spinning up heavy analysis runs / Celery
            columns_arg: list[str] = []
            for tool in plan.tools:
                if tool.name == "file_qa":
                    columns_arg.extend(tool.arguments.get("columns") or [])
            target_columns = columns_arg or active_columns

            cache_key = build_analysis_cache_key(
                str(dataset_version.id),
                "file_qa",
                {
                    "question": question.strip().lower(),
                    "columns": sorted(target_columns) if target_columns else [],
                },
            )
            cached = get_cached_result(cache_key)
            if cached is not None:
                interpretation = AnalysisInterpretation.model_validate(cached)
            else:
                parsed_file = _parse_dataset_file(
                    dataset_version,
                    selected_columns=target_columns,
                )
                interpretation = self.interpreter.interpret_file_qa(
                    question=question,
                    parsed_file=parsed_file,
                    history=history,
                )
                set_cached_result(cache_key, interpretation.model_dump(mode="json"))

            assistant_message = _assistant_text_from_interpretation(
                interpretation.answer,
                interpretation.key_findings,
            )

            assistant_message_record = None
            if persist_messages:
                assistant_message_record = save_message(
                    db=db,
                    user_id=user_id,
                    dataset_id=dataset_id,
                    role="assistant",
                    content=assistant_message,
                    analysis_run_id=None,
                )

            return AgentRunResult(
                dataset_id=dataset.id,
                dataset_version_id=dataset_version.id,
                question=question,
                plan=plan,
                analysis_run_id=None,
                interpretation=interpretation,
                assistant_message=assistant_message,
                user_message_id=user_message_record.id if user_message_record else None,
                assistant_message_id=assistant_message_record.id if assistant_message_record else None,
            )

        run = create_analysis_run(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
            tools=[
                {
                    "name": tool.name,
                    "arguments": tool.arguments,
                }
                for tool in eda_tools
            ],
            include_plots=any(
                bool(tool.arguments.get("include_plots"))
                for tool in eda_tools
            ),
        )
        interpretation = self.interpreter.interpret(
            question=question,
            dataset_context=context,
            plan=plan,
            tool_results=run.results_json or {},
            tool_errors=run.error_json,
        )
        assistant_message = _assistant_text_from_interpretation(
            interpretation.answer,
            interpretation.key_findings,
        )

        stored_run = db.get(AnalysisRun, run.id)
        if stored_run is not None:
            stored_run.results_json = {
                **(stored_run.results_json or {}),
                "_agent": {
                    "question": question,
                    "plan": plan.model_dump(mode="json"),
                    "interpretation": interpretation.model_dump(mode="json"),
                },
            }
            db.commit()
            db.refresh(stored_run)

        assistant_message_record = None
        if persist_messages:
            assistant_message_record = save_message(
                db=db,
                user_id=user_id,
                dataset_id=dataset_id,
                role="assistant",
                content=assistant_message,
                analysis_run_id=run.id,
            )

        return AgentRunResult(
            dataset_id=dataset.id,
            dataset_version_id=dataset_version.id,
            question=question,
            plan=plan,
            analysis_run_id=run.id,
            interpretation=interpretation,
            assistant_message=assistant_message,
            user_message_id=user_message_record.id if user_message_record else None,
            assistant_message_id=assistant_message_record.id if assistant_message_record else None,
        )


def run_analysis_agent(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
    question: str,
    active_columns: list[str] | None = None,
    history: list[ConversationTurn] | None = None,
    persist_messages: bool = True,
) -> AgentRunResult:
    return AnalysisAgentOrchestrator().run(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        question=question,
        active_columns=active_columns,
        history=history,
        persist_messages=persist_messages,
    )
