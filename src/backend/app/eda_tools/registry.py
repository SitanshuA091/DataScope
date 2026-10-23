from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.eda_tools.column import analyze_columns
from app.eda_tools.high_level import analyze_high_level
from app.eda_tools.quality import analyze_data_quality
from app.eda_tools.relationships import analyze_relationships

ToolFunction = Callable[..., dict[str, object]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    function: ToolFunction
    arguments: dict[str, Any]

    def planner_view(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


def analyze_file_qa(
    frame: pd.DataFrame,
    columns: list[str] | None = None,
    **_kwargs: Any,
) -> dict[str, object]:
    cols = [c for c in columns if c in frame.columns] if columns else list(frame.columns)
    sub = frame[cols] if cols else frame
    return {
        "tool": "file_qa",
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "selected_columns": list(sub.columns),
        "sample_rows": sub.head(25).to_dict(orient="records"),
    }


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "file_qa": ToolSpec(
        name="file_qa",
        description=(
            "Direct dataset file Q&A: parses sample rows, column types, and file structure to answer questions directly via the LLM client without running heavy statistical analysis."
        ),
        function=analyze_file_qa,
        arguments={
            "columns": "list[str], optional list of columns relevant to the question",
        },
    ),
    "high_level": ToolSpec(
        name="high_level",
        description=(
            "Dataset-level summary: shape, dtypes, missingness, duplicates, "
            "numeric summaries, categorical summaries, and optional overview plots."
        ),
        function=analyze_high_level,
        arguments={
            "include_plots": "bool, optional",
            "artifact_dir": "str/path, optional when include_plots is true",
        },
    ),
    "column": ToolSpec(
        name="column",
        description=(
            "Column-specific analysis using dtype-aware describe(), value counts, "
            "cardinality, quantiles, distributions, and optional plots."
        ),
        function=analyze_columns,
        arguments={
            "columns": "list[str], optional; defaults to all columns",
            "top_n": "int, optional number of values for categorical summaries",
            "include_plots": "bool, optional",
            "artifact_dir": "str/path, optional when include_plots is true",
        },
    ),
    "relationships": ToolSpec(
        name="relationships",
        description=(
            "Relationship analysis for selected variables: numeric correlations, "
            "strongest pairs, grouped statistics, and optional scatter/box/heatmap plots."
        ),
        function=analyze_relationships,
        arguments={
            "columns": "list[str], optional; defaults to all columns",
            "include_plots": "bool, optional",
            "artifact_dir": "str/path, optional when include_plots is true",
        },
    ),
    "quality": ToolSpec(
        name="quality",
        description=(
            "Data quality checks: missingness, duplicate rows, constant columns, "
            "high-cardinality text columns, numeric outliers, and suspicious values."
        ),
        function=analyze_data_quality,
        arguments={
            "high_cardinality_threshold": "float, optional; default 0.9",
        },
    ),
}


def list_tools() -> list[dict[str, Any]]:
    return [tool.planner_view() for tool in TOOL_REGISTRY.values()]


def get_tool(name: str) -> ToolSpec:
    try:
        return TOOL_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown EDA tool: {name}") from exc


def run_tool(
    name: str,
    frame: pd.DataFrame,
    **kwargs: Any,
) -> dict[str, object]:
    tool = get_tool(name)
    sig = inspect.signature(tool.function)
    has_var_keyword = any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in sig.parameters.values()
    )
    if has_var_keyword:
        filtered_kwargs = kwargs
    else:
        filtered_kwargs = {
            k: v for k, v in kwargs.items()
            if k in sig.parameters
        }
    return tool.function(frame, **filtered_kwargs)
