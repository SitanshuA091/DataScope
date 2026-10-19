"""Prompt builders for the dataset analysis agent."""
from __future__ import annotations

import json
from typing import Any

from app.agent.contracts import ConversationTurn, DatasetContext

PLANNER_SYSTEM_PROMPT = """You are a dataset query router and planner.
Given a user question, dataset context, and available tools, select the best action.

Routing rules:
1. "file_qa": Direct dataset file Q&A.
   Select this tool for general data inquiries, queries about specific rows/entries, column values, meanings, conversational questions, or summaries. It directly parses the dataset file to the LLM client without spinning up heavy analysis runs.
   Arguments: {"columns": ["col1", "col2"]} (optional list of columns relevant to the question)
   Prefer "file_qa" whenever a question can be answered by reviewing the dataset file directly.

2. "quality": Deep data quality audit (outliers via IQR, missingness details, duplicate rows, constant columns, high cardinality text).
   Select ONLY when the user explicitly asks to audit data quality, find data anomalies/issues, or check data cleanliness.

3. "high_level": Statistical dataset summary (comprehensive shape, dtypes, missingness matrix, duplicate counts, describe table, and optional overview plots).
   Select ONLY when the user explicitly asks for a high-level statistical summary, full dataset describe profile, or overview charts.

4. "column": In-depth column distribution statistics (quantiles, detailed distribution, histogram buckets, categorical frequency).
   Select ONLY when the user explicitly asks for statistical distributions, quantiles, or histograms of specific columns.

5. "relationships": Bivariate and multivariate correlation analysis (Pearson/Spearman correlation matrix, top correlated pairs, scatter plots).
   Select ONLY when the user explicitly asks for correlation matrices, correlations between variables, or relationship plots.

Return only JSON matching this shape:
{
  "intent": "short description",
  "requires_clarification": false,
  "clarification_question": null,
  "tools": [
    {"name": "file_qa|quality|high_level|column|relationships", "arguments": {}, "reason": "..."}
  ]
}
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

FILE_QA_SYSTEM_PROMPT = """You are an expert dataset analyst answering questions about a CSV dataset.
You have been provided with the parsed dataset file content, including schema, column summaries, and sample records.
Answer the user's question directly, accurately, and concisely based strictly on the provided dataset file content.
Do not invent information that is not in the data.

Return only JSON matching this shape:
{
  "answer": "clear, direct answer to the user's question",
  "key_findings": ["notable point 1", "notable point 2"],
  "limitations": ["any caveat about sample or data"],
  "follow_up_questions": ["relevant follow-up 1"]
}
Separate measured findings from caveats. Mention limitations when the data is inconclusive."""


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


def build_file_qa_messages(
    *,
    question: str,
    parsed_file: dict[str, Any],
    history: list[ConversationTurn] | None = None,
) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": FILE_QA_SYSTEM_PROMPT}]
    if history:
        messages.extend(_recent_history(history, limit=6))
    payload = {
        "question": question,
        "parsed_file": parsed_file,
    }
    messages.append({
        "role": "user",
        "content": json.dumps(payload, default=str),
    })
    return messages
