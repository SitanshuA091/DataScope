from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.eda_tools.column import analyze_columns
from app.eda_tools.high_level import analyze_high_level
from app.eda_tools.quality import analyze_data_quality
from app.eda_tools.registry import list_tools, run_tool
from app.eda_tools.relationships import analyze_relationships


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [25, 35, 45, 55, 1000],
            "income": [50_000, 65_000, 80_000, np.nan, 120_000],
            "segment": ["a", "a", "b", "b", " "],
            "constant": [1, 1, 1, 1, 1],
            "customer_id": ["c1", "c2", "c3", "c4", "c5"],
        }
    )


def test_high_level_analysis_returns_dataset_summary() -> None:
    result = analyze_high_level(_frame())

    assert result["tool"] == "high_level"
    assert result["shape"] == {"rows": 5, "columns": 5}
    assert result["missing_values"]["total_missing_cells"] == 1
    assert "age" in result["numeric_summary"]
    assert result["column_type_counts"]["numeric"] == 3


def test_column_analysis_uses_dtype_appropriate_details() -> None:
    result = analyze_columns(_frame(), ["age", "segment"], top_n=2)

    age, segment = result["results"]
    assert age["column"] == "age"
    assert age["inferred_type"] == "numeric"
    assert age["outliers"]["count"] == 1
    assert segment["inferred_type"] == "categorical"
    assert segment["top_values"][0]["value"] == "a"


def test_relationship_analysis_returns_correlations_and_grouped_stats() -> None:
    result = analyze_relationships(_frame(), ["age", "income", "segment"])

    assert result["tool"] == "relationships"
    assert result["numeric_columns"] == ["age", "income"]
    assert result["correlations"]["top_pairs"][0]["left"] == "age"
    assert result["grouped_statistics"][0]["category_column"] == "segment"


def test_quality_analysis_detects_common_issues() -> None:
    result = analyze_data_quality(_frame())

    assert result["missingness"][0]["column"] == "income"
    assert result["constant_columns"] == [{"column": "constant", "value": 1}]
    assert result["numeric_outliers"][0]["column"] == "age"
    assert result["suspicious_values"]["whitespace_only_strings"][0] == {
        "column": "segment",
        "count": 1,
    }


def test_registry_exposes_and_runs_tools() -> None:
    names = {tool["name"] for tool in list_tools()}

    assert {"high_level", "column", "relationships", "quality"} <= names
    assert run_tool("quality", _frame())["tool"] == "quality"
