"""Planner that selects controlled EDA tools for a user question."""
from __future__ import annotations

from typing import Any

from app.agent.contracts import AgentPlan, ConversationTurn, DatasetContext
from app.agent.prompts import build_planner_messages
from app.core.config import settings
from app.core.exceptions import AppError
from app.eda_tools.registry import TOOL_REGISTRY, list_tools
from app.integrations.llm_client import LiteLLMClient, LLMClient


class AgentPlanningError(AppError):
    error_code = "agent_planning_error"
    default_message = "The agent could not create a valid analysis plan."


def _validate_tool_arguments(
    *,
    plan: AgentPlan,
    dataset_context: DatasetContext,
) -> AgentPlan:
    available_columns = dataset_context.column_names
    seen_tools: set[tuple[str, str]] = set()

    for tool in plan.tools:
        if tool.name not in TOOL_REGISTRY:
            raise AgentPlanningError(
                "The planner selected an unsupported tool.",
                details={"tool": tool.name},
            )

        columns = tool.arguments.get("columns")
        if columns is not None:
            missing = [
                column for column in columns if column not in available_columns
            ]
            if missing:
                raise AgentPlanningError(
                    "The planner selected columns that are not in the dataset.",
                    details={"tool": tool.name, "missing_columns": missing},
                )

        identity = (tool.name, repr(sorted(tool.arguments.items())))
        if identity in seen_tools:
            raise AgentPlanningError(
                "The planner selected duplicate tool calls.",
                details={"tool": tool.name},
            )
        seen_tools.add(identity)

    return plan


class AgentPlanner:
    def __init__(
        self,
        *,
        llm_client: LLMClient | None = None,
        planner_model: str | None = None,
    ) -> None:
        default_client = LiteLLMClient(planner_model=planner_model)
        self.llm_client = llm_client or default_client
        self.model = planner_model or getattr(
            self.llm_client,
            "planner_model",
            settings.planner_model,
        )

    def plan(
        self,
        *,
        question: str,
        dataset_context: DatasetContext,
        history: list[ConversationTurn] | None = None,
    ) -> AgentPlan:
        messages = build_planner_messages(
            question=question,
            dataset_context=dataset_context,
            available_tools=list_tools(),
            history=history,
        )
        raw_plan: dict[str, Any] = self.llm_client.complete_json(
            model=self.model,
            messages=messages,
            temperature=0.0,
        )
        try:
            plan = AgentPlan.model_validate(raw_plan)
        except ValueError as exc:
            raise AgentPlanningError(
                "The planner returned invalid structured output.",
                details={"error": str(exc)},
            ) from exc

        if len(plan.tools) > settings.max_tools_per_run:
            raise AgentPlanningError(
                "The planner selected too many tools.",
                details={
                    "selected": len(plan.tools),
                    "limit": settings.max_tools_per_run,
                },
            )

        return _validate_tool_arguments(
            plan=plan,
            dataset_context=dataset_context,
        )
