from __future__ import annotations

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


TOOL_REGISTRY: dict[str, ToolSpec] = {
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
    return tool.function(frame, **kwargs)
