from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _artifact_path(artifact_dir: Path | str, prefix: str) -> Path:
    directory = Path(artifact_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{prefix}_{uuid4().hex}.png"


def _finish_plot(path: Path, title: str, columns: list[str], kind: str) -> dict[str, object]:
    plt.tight_layout()
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close()
    return {
        "kind": kind,
        "title": title,
        "path": str(path),
        "columns": columns,
        "format": "png",
    }


def histogram(
    frame: pd.DataFrame,
    column: str,
    artifact_dir: Path | str,
    *,
    bins: int = 30,
) -> dict[str, object]:
    values = frame[column].dropna()
    path = _artifact_path(artifact_dir, f"histogram_{column}")
    plt.figure(figsize=(7, 4))
    sns.histplot(values, bins=bins, kde=True)
    plt.title(f"Distribution of {column}")
    plt.xlabel(column)
    plt.ylabel("Count")
    return _finish_plot(path, f"Distribution of {column}", [column], "histogram")


def value_counts_bar(
    frame: pd.DataFrame,
    column: str,
    artifact_dir: Path | str,
    *,
    top_n: int = 15,
) -> dict[str, object]:
    counts = frame[column].value_counts(dropna=False).head(top_n)
    path = _artifact_path(artifact_dir, f"value_counts_{column}")
    plt.figure(figsize=(8, 4.5))
    sns.barplot(x=counts.values, y=[str(value) for value in counts.index], orient="h")
    plt.title(f"Top values for {column}")
    plt.xlabel("Count")
    plt.ylabel(column)
    return _finish_plot(path, f"Top values for {column}", [column], "bar")


def correlation_heatmap(
    frame: pd.DataFrame,
    artifact_dir: Path | str,
    *,
    columns: list[str] | None = None,
) -> dict[str, object] | None:
    numeric = frame.select_dtypes(include="number")
    if columns is not None:
        numeric = numeric[[column for column in columns if column in numeric.columns]]
    if numeric.shape[1] < 2:
        return None

    corr = numeric.corr()
    path = _artifact_path(artifact_dir, "correlation_heatmap")
    plt.figure(figsize=(max(7, corr.shape[1] * 0.8), max(5, corr.shape[0] * 0.65)))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, square=False)
    plt.title("Correlation heatmap")
    return _finish_plot(path, "Correlation heatmap", list(corr.columns), "heatmap")


def scatter_plot(
    frame: pd.DataFrame,
    x: str,
    y: str,
    artifact_dir: Path | str,
) -> dict[str, object]:
    path = _artifact_path(artifact_dir, f"scatter_{x}_{y}")
    plt.figure(figsize=(6.5, 4.5))
    sns.scatterplot(data=frame, x=x, y=y)
    plt.title(f"{y} vs {x}")
    return _finish_plot(path, f"{y} vs {x}", [x, y], "scatter")


def box_plot(
    frame: pd.DataFrame,
    category: str,
    numeric: str,
    artifact_dir: Path | str,
) -> dict[str, object]:
    path = _artifact_path(artifact_dir, f"box_{category}_{numeric}")
    plt.figure(figsize=(8, 4.5))
    sns.boxplot(data=frame, x=category, y=numeric)
    plt.title(f"{numeric} by {category}")
    plt.xticks(rotation=30, ha="right")
    return _finish_plot(path, f"{numeric} by {category}", [category, numeric], "box")
