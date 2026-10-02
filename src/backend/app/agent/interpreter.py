"""Grounded interpretation of computed EDA tool output."""
from __future__ import annotations

from typing import Any

from app.agent.contracts import AgentPlan, AnalysisInterpretation, DatasetContext
from app.agent.prompts import build_interpreter_messages
from app.core.config import settings
from app.core.exceptions import AppError
from app.integrations.llm_client import LiteLLMClient, LLMClient


class AgentInterpretationError(AppError):
    error_code = "agent_interpretation_error"
    default_message = "The agent could not interpret the analysis results."


class AgentInterpreter:
    def __init__(
        self,
        *,
        llm_client: LLMClient | None = None,
        interpreter_model: str | None = None,
    ) -> None:
        default_client = LiteLLMClient(interpreter_model=interpreter_model)
        self.llm_client = llm_client or default_client
        self.model = interpreter_model or getattr(
            self.llm_client,
            "interpreter_model",
            settings.interpreter_model,
        )

    def interpret(
        self,
        *,
        question: str,
        dataset_context: DatasetContext,
        plan: AgentPlan,
        tool_results: dict[str, Any],
        tool_errors: dict[str, Any] | None = None,
    ) -> AnalysisInterpretation:
        messages = build_interpreter_messages(
            question=question,
            dataset_context=dataset_context,
            plan=plan.model_dump(mode="json"),
            tool_results=tool_results,
            tool_errors=tool_errors,
        )
        raw = self.llm_client.complete_json(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        try:
            return AnalysisInterpretation.model_validate(raw)
        except ValueError as exc:
            raise AgentInterpretationError(
                "The interpreter returned invalid structured output.",
                details={"error": str(exc)},
            ) from exc
