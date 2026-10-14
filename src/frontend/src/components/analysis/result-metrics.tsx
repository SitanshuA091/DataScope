import { formatNumber } from "@/lib/formatters";

function summarizeToolMetrics(
  toolName: string,
  value: unknown,
): Array<{ label: string; display: string }> {
  if (!value || typeof value !== "object") {
    return [{ label: toolName, display: String(value) }];
  }

  const data = value as Record<string, unknown>;
  const items: Array<{ label: string; display: string }> = [];

  if (toolName === "high_level") {
    const shape = data.shape as { rows?: number; columns?: number } | undefined;
    if (shape?.rows != null && shape?.columns != null) {
      items.push({
        label: "Shape",
        display: `${formatNumber(shape.rows, 0)} × ${formatNumber(shape.columns, 0)}`,
      });
    }
    const missing = data.missing_values as
      | { total_missing_cells?: number }
      | undefined;
    if (missing?.total_missing_cells != null) {
      items.push({
        label: "Missing cells",
        display: formatNumber(missing.total_missing_cells, 0),
      });
    }
    const duplicates = data.duplicate_rows as { count?: number } | undefined;
    if (duplicates?.count != null) {
      items.push({
        label: "Duplicate rows",
        display: formatNumber(duplicates.count, 0),
      });
    }
  }

  if (toolName === "quality") {
    if (typeof data.row_count === "number") {
      items.push({
        label: "Rows scanned",
        display: formatNumber(data.row_count, 0),
      });
    }
    const missing = Array.isArray(data.missingness) ? data.missingness : [];
    items.push({
      label: "Columns with missing",
      display: formatNumber(missing.length, 0),
    });
  }

  if (toolName === "column") {
    const results = Array.isArray(data.results) ? data.results : [];
    items.push({
      label: "Columns analyzed",
      display: formatNumber(results.length, 0),
    });
  }

  if (toolName === "relationships") {
    const pairs =
      data.correlations &&
      typeof data.correlations === "object" &&
      Array.isArray((data.correlations as { top_pairs?: unknown }).top_pairs)
        ? ((data.correlations as { top_pairs: unknown[] }).top_pairs)
        : [];
    items.push({
      label: "Top correlations",
      display: formatNumber(pairs.length, 0),
    });
  }

  if (items.length === 0) {
    items.push({
      label: toolName.replaceAll("_", " "),
      display: "Results ready",
    });
  }

  return items;
}

export function ResultMetrics({
  results,
  metrics,
}: {
  results?: Record<string, unknown> | null;
  metrics?: Record<string, unknown> | null;
}) {
  const source = metrics ?? results;
  if (!source || Object.keys(source).length === 0) {
    return <p className="text-sm text-slate-600">No results available yet.</p>;
  }

  const tiles = Object.entries(source)
    .filter(([key]) => key !== "_agent")
    .flatMap(([toolName, value]) => summarizeToolMetrics(toolName, value))
    .slice(0, 6);

  return (
    <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {tiles.map((tile, index) => (
        <div
          className="rounded-md bg-slate-50 p-3"
          key={`${tile.label}-${index}`}
        >
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {tile.label}
          </dt>
          <dd className="mt-1 truncate text-sm font-semibold text-slate-950">
            {tile.display}
          </dd>
        </div>
      ))}
    </dl>
  );
}
