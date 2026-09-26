from __future__ import annotations

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
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _json_dict(values: dict[Any, Any]) -> dict[str, Any]:
    return {str(key): _json_value(value) for key, value in values.items()}


def _describe(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if frame.empty:
        return {}
    return {
        column: _json_dict(stats)
        for column, stats in frame.describe().to_dict().items()
    }


def _missing_summary(frame: pd.DataFrame) -> dict[str, object]:
    missing = frame.isna().sum().sort_values(ascending=False)
    rows = len(frame)
    by_column = [
        {
            "column": str(column),
            "missing_count": int(count),
            "missing_percent": float(count / rows * 100) if rows else 0.0,
        }
        for column, count in missing.items()
        if int(count) > 0
    ]
    return {
        "total_missing_cells": int(missing.sum()),
        "columns_with_missing_values": len(by_column),
        "by_column": by_column,
    }


def _column_overview(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows = len(frame)
    return [
        {
            "name": str(column),
            "dtype": str(frame[column].dtype),
            "missing_count": int(frame[column].isna().sum()),
            "missing_percent": (
                float(frame[column].isna().mean() * 100) if rows else 0.0
            ),
            "unique_count": int(frame[column].nunique(dropna=True)),
            "unique_percent": (
                float(frame[column].nunique(dropna=True) / rows * 100)
                if rows
                else 0.0
            ),
        }
        for column in frame.columns
    ]


def _distribution_summary(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    numeric = frame.select_dtypes(include="number")
    if numeric.empty:
        return {}
    summary: dict[str, dict[str, Any]] = {}
    for column in numeric.columns:
        series = numeric[column].dropna()
        summary[str(column)] = {
            "skew": _json_value(series.skew()) if not series.empty else None,
            "kurtosis": _json_value(series.kurtosis()) if len(series) > 1 else None,
            "zero_count": int((series == 0).sum()),
            "negative_count": int((series < 0).sum()),
        }
    return summary


def analyze_high_level(
    frame: pd.DataFrame,
    *,
    include_plots: bool = False,
    artifact_dir: Path | str | None = None,
) -> dict[str, object]:
    """Return dataset-level EDA metrics for planner-selected high-level analysis."""

    numeric = frame.select_dtypes(include="number")
    categorical = frame.select_dtypes(include=["object", "str", "category", "bool"])
    datetime_columns = frame.select_dtypes(include=["datetime", "datetimetz"])
    artifacts: list[dict[str, object]] = []

    if include_plots and artifact_dir is not None:
        for column in numeric.columns[:3]:
            artifacts.append(plotting.histogram(frame, str(column), artifact_dir))
        heatmap = plotting.correlation_heatmap(frame, artifact_dir)
        if heatmap is not None:
            artifacts.append(heatmap)

    return {
        "tool": "high_level",
        "shape": {"rows": int(frame.shape[0]), "columns": int(frame.shape[1])},
        "columns": _column_overview(frame),
        "dtype_counts": _json_dict(frame.dtypes.astype(str).value_counts().to_dict()),
        "column_type_counts": {
            "numeric": int(numeric.shape[1]),
            "categorical": int(categorical.shape[1]),
            "datetime": int(datetime_columns.shape[1]),
        },
        "memory_usage_bytes": int(frame.memory_usage(deep=True).sum()),
        "missing_values": _missing_summary(frame),
        "duplicate_rows": {
            "count": int(frame.duplicated().sum()),
            "percent": float(frame.duplicated().mean() * 100) if len(frame) else 0.0,
        },
        "numeric_summary": _describe(numeric),
        "categorical_summary": _describe(categorical),
        "numeric_distributions": _distribution_summary(frame),
        "artifacts": artifacts,
    }
