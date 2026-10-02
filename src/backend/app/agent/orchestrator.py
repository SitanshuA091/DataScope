"""Dataset-agent orchestration flow.

Coordinates context retrieval, tool planning, analysis execution, grounded
interpretation, and optional conversation persistence.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.agent.contracts import (
    AgentRunResult,
    ConversationTurn,
    DatasetColumn,
    DatasetContext,
)
from app.agent.interpreter import AgentInterpreter
from app.agent.planner import AgentPlanner
from app.db.models.analysis_run import AnalysisRun
from app.services.analysis_service import create_analysis_run
from app.services.context_service import save_message
from app.services.dataset_service import get_dataset_overview


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

        if persist_messages:
            save_message(
                db=db,
                user_id=user_id,
                dataset_id=dataset_id,
                role="user",
                content=question,
            )

        if plan.requires_clarification:
            assistant_message = plan.clarification_question or "Can you clarify?"
            if persist_messages:
                save_message(
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
                for tool in plan.tools
            ],
            include_plots=any(
                bool(tool.arguments.get("include_plots"))
                for tool in plan.tools
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

        if persist_messages:
            save_message(
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
