from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.eda_tools import plotting


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def _validate_columns(frame: pd.DataFrame, columns: list[str] | None) -> list[str]:
    selected = list(frame.columns) if columns is None else columns
    missing = [column for column in selected if column not in frame.columns]
    if missing:
        raise ValueError(f"Columns not found in dataframe: {missing}")
    return [str(column) for column in selected]


def _correlation_summary(numeric: pd.DataFrame) -> dict[str, object]:
    if numeric.shape[1] < 2:
        return {"matrix": {}, "top_pairs": []}

    corr = numeric.corr()
    top_pairs = []
    for left, right in combinations(corr.columns, 2):
        value = corr.loc[left, right]
        if pd.isna(value):
            continue
        top_pairs.append(
            {
                "left": str(left),
                "right": str(right),
                "correlation": float(value),
                "absolute_correlation": abs(float(value)),
            }
        )
    top_pairs.sort(key=lambda item: item["absolute_correlation"], reverse=True)

    return {
        "matrix": {
            str(column): {
                str(index): _json_value(value)
                for index, value in corr[column].to_dict().items()
            }
            for column in corr.columns
        },
        "top_pairs": top_pairs[:10],
    }


def _grouped_stats(
    frame: pd.DataFrame,
    categorical_columns: list[str],
    numeric_columns: list[str],
    *,
    max_groups: int = 20,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for category in categorical_columns:
        if frame[category].nunique(dropna=True) > max_groups:
            continue
        for numeric in numeric_columns:
            grouped = frame.groupby(category, dropna=False)[numeric].agg(
                ["count", "mean", "median", "std", "min", "max"]
            )
            records = []
            for group_value, stats in grouped.iterrows():
                records.append(
                    {
                        "group": _json_value(group_value),
                        "count": int(stats["count"]),
                        "mean": _json_value(stats["mean"]),
                        "median": _json_value(stats["median"]),
                        "std": _json_value(stats["std"]),
                        "min": _json_value(stats["min"]),
                        "max": _json_value(stats["max"]),
                    }
                )
            results.append(
                {
                    "category_column": category,
                    "numeric_column": numeric,
                    "groups": records,
                }
            )
    return results


def analyze_relationships(
    frame: pd.DataFrame,
    columns: list[str] | None = None,
    *,
    include_plots: bool = False,
    artifact_dir: Path | str | None = None,
) -> dict[str, object]:
    """Analyze correlations and grouped relationships for selected variables."""

    selected = _validate_columns(frame, columns)
    scoped = frame[selected]
    numeric_columns = [
        str(column)
        for column in scoped.select_dtypes(include="number").columns
    ]
    categorical_columns = [
        str(column)
        for column in scoped.select_dtypes(
            include=["object", "str", "category", "bool"]
        ).columns
    ]
    numeric = scoped[numeric_columns]
    artifacts: list[dict[str, object]] = []

    if include_plots and artifact_dir is not None:
        heatmap = plotting.correlation_heatmap(scoped, artifact_dir)
        if heatmap is not None:
            artifacts.append(heatmap)
        for left, right in combinations(numeric_columns[:4], 2):
            artifacts.append(plotting.scatter_plot(scoped, left, right, artifact_dir))
        for category in categorical_columns[:2]:
            for numeric_column in numeric_columns[:2]:
                artifacts.append(
                    plotting.box_plot(scoped, category, numeric_column, artifact_dir)
                )

    return {
        "tool": "relationships",
        "columns": selected,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "correlations": _correlation_summary(numeric),
        "grouped_statistics": _grouped_stats(
            scoped,
            categorical_columns,
            numeric_columns,
        ),
        "artifacts": artifacts,
    }
