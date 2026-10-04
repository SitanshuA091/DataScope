"""Prompt builders for the dataset analysis agent."""
from __future__ import annotations

import json
from typing import Any

from app.agent.contracts import ConversationTurn, DatasetContext

PLANNER_SYSTEM_PROMPT = """You plan controlled EDA work for a CSV dataset.
Return only JSON matching this shape:
{
  "intent": "short description",
  "requires_clarification": false,
  "clarification_question": null,
  "tools": [
    {"name": "quality|high_level|column|relationships", "arguments": {}, "reason": "..."}
  ]
}
Use only available tools. Do not invent columns. Prefer one or two tools unless the request clearly needs more.
For ambiguous issue-finding requests, choose quality. For schema/type questions, choose high_level.
For "that", "previous", or selected-column references, use active_columns when available.
Ask a clarification question only when the request cannot be answered with the schema, active columns, or history."""

INTERPRETER_SYSTEM_PROMPT = """You explain computed EDA results.
Use only the supplied structured tool output and relevant dataset/tool context.
Do not invent metrics, column names, rows, charts, or causal claims.
Return only JSON matching this shape:
{
  "answer": "concise answer grounded in the tool output",
  "key_findings": ["..."],
  "limitations": ["..."],
  "follow_up_questions": ["..."]
}
Separate measured findings from caveats. Mention limitations when the tool output is incomplete or failed."""


def _dataset_payload(context: DatasetContext) -> dict[str, Any]:
    return {
        "dataset_id": str(context.dataset_id),
        "dataset_version_id": str(context.dataset_version_id),
        "row_count": context.row_count,
        "column_count": context.column_count,
        "columns": [column.model_dump() for column in context.columns],
        "active_columns": context.active_columns,
    }


def _interpretation_context_payload(context: DatasetContext) -> dict[str, Any]:
    return {
        "dataset_id": str(context.dataset_id),
        "dataset_version_id": str(context.dataset_version_id),
        "row_count": context.row_count,
        "column_count": context.column_count,
        "active_columns": context.active_columns,
    }


def _tool_context_payload(plan: dict[str, Any]) -> list[dict[str, Any]]:
    tools = plan.get("tools") or []
    return [
        {
            "name": tool.get("name"),
            "arguments": tool.get("arguments") or {},
        }
        for tool in tools
        if isinstance(tool, dict)
    ]


def _recent_history(history: list[ConversationTurn], *, limit: int = 8) -> list[dict[str, str]]:
    return [
        turn.model_dump()
        for turn in history[-limit:]
    ]


def build_planner_messages(
    *,
    question: str,
    dataset_context: DatasetContext,
    available_tools: list[dict[str, Any]],
    history: list[ConversationTurn] | None = None,
) -> list[dict[str, str]]:
    payload = {
        "question": question,
        "dataset": _dataset_payload(dataset_context),
        "available_tools": available_tools,
        "recent_history": _recent_history(history or []),
    }
    return [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, default=str)},
    ]


def build_interpreter_messages(
    *,
    question: str,
    dataset_context: DatasetContext,
    plan: dict[str, Any],
    tool_results: dict[str, Any],
    tool_errors: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    payload = {
        "question": question,
        "dataset_context": _interpretation_context_payload(dataset_context),
        "tools": _tool_context_payload(plan),
        "tool_results": tool_results,
        "tool_errors": tool_errors or {},
    }
    return [
        {"role": "system", "content": INTERPRETER_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, default=str)},
    ]
