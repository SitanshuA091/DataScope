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


def _series_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "categorical"


def _describe_series(series: pd.Series) -> dict[str, Any]:
    described = series.describe()
    return {str(key): _json_value(value) for key, value in described.items()}


def _numeric_details(series: pd.Series) -> dict[str, Any]:
    clean = series.dropna()
    if clean.empty:
        return {"quantiles": {}, "outliers": {"count": 0, "lower_bound": None, "upper_bound": None}}

    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = clean[(clean < lower) | (clean > upper)]
    return {
        "quantiles": {
            "p01": _json_value(clean.quantile(0.01)),
            "p05": _json_value(clean.quantile(0.05)),
            "p25": _json_value(q1),
            "p50": _json_value(clean.quantile(0.50)),
            "p75": _json_value(q3),
            "p95": _json_value(clean.quantile(0.95)),
            "p99": _json_value(clean.quantile(0.99)),
        },
        "skew": _json_value(clean.skew()),
        "kurtosis": _json_value(clean.kurtosis()) if len(clean) > 1 else None,
        "outliers": {
            "method": "iqr_1_5",
            "count": int(outliers.count()),
            "percent": float(outliers.count() / len(clean) * 100),
            "lower_bound": _json_value(lower),
            "upper_bound": _json_value(upper),
        },
    }


def _categorical_details(series: pd.Series, top_n: int) -> dict[str, Any]:
    counts = series.value_counts(dropna=False).head(top_n)
    return {
        "top_values": [
            {
                "value": _json_value(index),
                "count": int(count),
                "percent": float(count / len(series) * 100) if len(series) else 0.0,
            }
            for index, count in counts.items()
        ],
    }


def _datetime_details(series: pd.Series) -> dict[str, Any]:
    clean = series.dropna()
    return {
        "min": _json_value(clean.min()) if not clean.empty else None,
        "max": _json_value(clean.max()) if not clean.empty else None,
    }


def _validate_columns(frame: pd.DataFrame, columns: list[str] | None) -> list[str]:
    selected = list(frame.columns) if columns is None else columns
    missing = [column for column in selected if column not in frame.columns]
    if missing:
        raise ValueError(f"Columns not found in dataframe: {missing}")
    return [str(column) for column in selected]


def analyze_columns(
    frame: pd.DataFrame,
    columns: list[str] | None = None,
    *,
    top_n: int = 10,
    include_plots: bool = False,
    artifact_dir: Path | str | None = None,
) -> dict[str, object]:
    """Analyze selected columns using dtype-appropriate pandas summaries."""

    selected = _validate_columns(frame, columns)
    results: list[dict[str, Any]] = []
    artifacts: list[dict[str, object]] = []

    for column in selected:
        series = frame[column]
        kind = _series_type(series)
        missing_count = int(series.isna().sum())
        result: dict[str, Any] = {
            "column": column,
            "dtype": str(series.dtype),
            "inferred_type": kind,
            "row_count": len(series),
            "missing_count": missing_count,
            "missing_percent": float(series.isna().mean() * 100) if len(series) else 0.0,
            "unique_count": int(series.nunique(dropna=True)),
            "cardinality_ratio": (
                float(series.nunique(dropna=True) / len(series)) if len(series) else 0.0
            ),
            "describe": _describe_series(series),
        }

        if kind == "numeric":
            result.update(_numeric_details(series))
            if include_plots and artifact_dir is not None:
                artifacts.append(plotting.histogram(frame, column, artifact_dir))
        elif kind == "datetime":
            result.update(_datetime_details(series))
        else:
            result.update(_categorical_details(series, top_n))
            if include_plots and artifact_dir is not None:
                artifacts.append(plotting.value_counts_bar(frame, column, artifact_dir))

        results.append(result)

    return {
        "tool": "column",
        "columns": selected,
        "results": results,
        "artifacts": artifacts,
    }
