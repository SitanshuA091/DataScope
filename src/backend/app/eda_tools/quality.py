from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def _missingness(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows = len(frame)
    missing = frame.isna().sum().sort_values(ascending=False)
    return [
        {
            "column": str(column),
            "missing_count": int(count),
            "missing_percent": float(count / rows * 100) if rows else 0.0,
        }
        for column, count in missing.items()
        if int(count) > 0
    ]


def _constant_columns(frame: pd.DataFrame) -> list[dict[str, object]]:
    constants = []
    for column in frame.columns:
        unique_count = frame[column].nunique(dropna=False)
        if unique_count <= 1:
            constants.append(
                {
                    "column": str(column),
                    "value": _json_value(frame[column].iloc[0]) if len(frame) else None,
                }
            )
    return constants


def _high_cardinality_columns(
    frame: pd.DataFrame,
    *,
    threshold: float,
) -> list[dict[str, object]]:
    rows = len(frame)
    if rows == 0:
        return []
    columns = []
    candidates = frame.select_dtypes(include=["object", "str", "category", "string"])
    for column in candidates.columns:
        unique_count = int(candidates[column].nunique(dropna=True))
        ratio = unique_count / rows
        if ratio >= threshold:
            columns.append(
                {
                    "column": str(column),
                    "unique_count": unique_count,
                    "cardinality_ratio": float(ratio),
                }
            )
    return columns


def _numeric_outliers(frame: pd.DataFrame) -> list[dict[str, object]]:
    results = []
    for column in frame.select_dtypes(include="number").columns:
        series = frame[column].dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        count = int(((series < lower) | (series > upper)).sum())
        if count:
            results.append(
                {
                    "column": str(column),
                    "method": "iqr_1_5",
                    "outlier_count": count,
                    "outlier_percent": float(count / len(series) * 100),
                    "lower_bound": _json_value(lower),
                    "upper_bound": _json_value(upper),
                }
            )
    return results


def _suspicious_values(frame: pd.DataFrame) -> dict[str, list[dict[str, object]]]:
    empty_strings = []
    whitespace_strings = []
    infinite_values = []

    text = frame.select_dtypes(include=["object", "str", "category", "string"])
    for column in text.columns:
        as_string = text[column].dropna().astype(str)
        empty_count = int((as_string == "").sum())
        whitespace_count = int((as_string.str.strip() == "").sum())
        if empty_count:
            empty_strings.append({"column": str(column), "count": empty_count})
        if whitespace_count:
            whitespace_strings.append({"column": str(column), "count": whitespace_count})

    numeric = frame.select_dtypes(include="number")
    for column in numeric.columns:
        count = int(np.isinf(numeric[column]).sum())
        if count:
            infinite_values.append({"column": str(column), "count": count})

    return {
        "empty_strings": empty_strings,
        "whitespace_only_strings": whitespace_strings,
        "infinite_numeric_values": infinite_values,
    }


def analyze_data_quality(
    frame: pd.DataFrame,
    *,
    high_cardinality_threshold: float = 0.9,
) -> dict[str, object]:
    """Detect common data quality issues without mutating the dataframe."""

    duplicate_count = int(frame.duplicated().sum())
    return {
        "tool": "quality",
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "missingness": _missingness(frame),
        "duplicate_rows": {
            "count": duplicate_count,
            "percent": float(duplicate_count / len(frame) * 100) if len(frame) else 0.0,
        },
        "constant_columns": _constant_columns(frame),
        "high_cardinality_columns": _high_cardinality_columns(
            frame,
            threshold=high_cardinality_threshold,
        ),
        "numeric_outliers": _numeric_outliers(frame),
        "suspicious_values": _suspicious_values(frame),
    }
