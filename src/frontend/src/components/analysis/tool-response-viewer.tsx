"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { formatBytes, formatNumber, formatPercent } from "@/lib/formatters";

type HighLevelData = {
  tool?: string;
  shape?: { rows: number; columns: number };
  memory_usage_bytes?: number;
  dtype_counts?: Record<string, number>;
  column_type_counts?: { numeric: number; categorical: number; datetime: number };
  missing_values?: {
    total_missing_cells: number;
    columns_with_missing_values: number;
    by_column?: Array<{ column: string; missing_count: number; missing_percent: number }>;
  };
  duplicate_rows?: { count: number; percent: number };
  numeric_summary?: Record<string, Record<string, number>>;
  categorical_summary?: Record<string, Record<string, string | number>>;
  numeric_distributions?: Record<string, { skew?: number; kurtosis?: number; zero_count?: number; negative_count?: number }>;
  artifacts?: Array<Record<string, unknown>>;
};

type QualityData = {
  tool?: string;
  row_count?: number;
  column_count?: number;
  missingness?: Array<{ column: string; missing_count: number; missing_percent: number }>;
  duplicate_rows?: { count: number; percent: number };
  constant_columns?: Array<{ column: string; value: unknown }>;
  high_cardinality_columns?: Array<{ column: string; unique_count?: number; cardinality_ratio?: number }>;
  numeric_outliers?: Array<{
    column: string;
    outlier_count?: number;
    lower_bound?: number;
    upper_bound?: number;
    sample_outliers?: number[];
  }>;
  suspicious_values?: {
    empty_strings?: Array<{ column: string; count: number }>;
    whitespace_only_strings?: Array<{ column: string; count: number }>;
    infinite_numeric_values?: Array<{ column: string; count: number }>;
  };
};

type ColumnResult = {
  column: string;
  dtype: string;
  inferred_type: string;
  row_count: number;
  missing_count: number;
  missing_percent: number;
  unique_count: number;
  cardinality_ratio?: number;
  describe?: Record<string, number | string>;
  quantiles?: Record<string, number>;
  skew?: number;
  kurtosis?: number;
  outliers?: { count: number; lower_bound?: number; upper_bound?: number };
  top_values?: Array<{ value: string; count: number; percent: number }>;
};

type ColumnData = {
  tool?: string;
  columns?: string[];
  results?: ColumnResult[];
  artifacts?: Array<Record<string, unknown>>;
};

type RelationshipData = {
  tool?: string;
  columns?: string[];
  numeric_columns?: string[];
  categorical_columns?: string[];
  correlations?: {
    matrix?: Record<string, Record<string, number>>;
    top_pairs?: Array<{ left: string; right: string; pearson_r: number; abs_r: number }>;
  };
  grouped_statistics?: Array<{
    category_column: string;
    numeric_column: string;
    groups: Array<{ category: string; count: number; mean: number; median: number; std?: number }>;
  }>;
  artifacts?: Array<Record<string, unknown>>;
};

type AgentData = {
  question?: string;
  plan?: {
    intent?: string;
    tools?: Array<{ name: string; arguments?: Record<string, unknown>; reason?: string }>;
  };
  interpretation?: {
    answer: string;
    key_findings: string[];
    limitations?: string[];
    follow_up_questions?: string[];
  };
};

export function HighLevelToolView({ data }: { data: HighLevelData }) {
  const shape = data.shape;
  const missing = data.missing_values;
  const duplicates = data.duplicate_rows;
  const numSummary = data.numeric_summary ?? {};
  const catSummary = data.categorical_summary ?? {};
  const numColumns = Object.keys(numSummary);
  const catColumns = Object.keys(catSummary);

  return (
    <div className="space-y-5">
      {/* Overview Stat Tiles */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-3.5">
          <p className="text-xs font-medium text-slate-500">Dimensions</p>
          <p className="mt-1 text-base font-bold text-slate-900">
            {shape ? `${formatNumber(shape.rows, 0)} × ${formatNumber(shape.columns, 0)}` : "N/A"}
          </p>
          <p className="text-[11px] text-slate-500">rows × columns</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-3.5">
          <p className="text-xs font-medium text-slate-500">Memory Usage</p>
          <p className="mt-1 text-base font-bold text-slate-900">
            {data.memory_usage_bytes ? formatBytes(data.memory_usage_bytes) : "N/A"}
          </p>
          <p className="text-[11px] text-slate-500">deep dataframe size</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-3.5">
          <p className="text-xs font-medium text-slate-500">Missing Cells</p>
          <p className={`mt-1 text-base font-bold ${missing?.total_missing_cells ? "text-amber-600" : "text-emerald-600"}`}>
            {missing ? formatNumber(missing.total_missing_cells, 0) : 0}
          </p>
          <p className="text-[11px] text-slate-500">
            in {missing?.columns_with_missing_values ?? 0} columns
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-3.5">
          <p className="text-xs font-medium text-slate-500">Duplicates</p>
          <p className={`mt-1 text-base font-bold ${duplicates?.count ? "text-amber-600" : "text-emerald-600"}`}>
            {duplicates ? formatNumber(duplicates.count, 0) : 0}
          </p>
          <p className="text-[11px] text-slate-500">
            {duplicates?.percent ? formatPercent(duplicates.percent) : "0.0%"}
          </p>
        </div>
      </div>

      {/* Column Types Breakdown */}
      {data.column_type_counts ? (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white p-3 text-xs">
          <span className="font-medium text-slate-700">Column Types:</span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-1 font-medium text-blue-700">
            Numeric: {data.column_type_counts.numeric}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-purple-50 px-2.5 py-1 font-medium text-purple-700">
            Categorical: {data.column_type_counts.categorical}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700">
            Datetime: {data.column_type_counts.datetime}
          </span>
        </div>
      ) : null}

      {/* Numeric Describe Table */}
      {numColumns.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Numeric Columns Summary ({numColumns.length})
          </h4>
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="border-b border-slate-200 bg-slate-50 font-medium text-slate-700">
                <tr>
                  <th className="px-3.5 py-2.5">Column</th>
                  <th className="px-3.5 py-2.5">Mean</th>
                  <th className="px-3.5 py-2.5">Std</th>
                  <th className="px-3.5 py-2.5">Min</th>
                  <th className="px-3.5 py-2.5">25%</th>
                  <th className="px-3.5 py-2.5">50% (Median)</th>
                  <th className="px-3.5 py-2.5">75%</th>
                  <th className="px-3.5 py-2.5">Max</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white font-mono text-[11px]">
                {numColumns.map((col) => {
                  const s = numSummary[col] ?? {};
                  return (
                    <tr className="hover:bg-slate-50" key={col}>
                      <td className="px-3.5 py-2 font-sans font-semibold text-slate-900">{col}</td>
                      <td className="px-3.5 py-2">{formatNumber(s.mean)}</td>
                      <td className="px-3.5 py-2">{formatNumber(s.std)}</td>
                      <td className="px-3.5 py-2">{formatNumber(s.min)}</td>
                      <td className="px-3.5 py-2">{formatNumber(s["25%"])}</td>
                      <td className="px-3.5 py-2 font-medium text-slate-950">{formatNumber(s["50%"])}</td>
                      <td className="px-3.5 py-2">{formatNumber(s["75%"])}</td>
                      <td className="px-3.5 py-2">{formatNumber(s.max)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Categorical Describe Table */}
      {catColumns.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Categorical Columns Summary ({catColumns.length})
          </h4>
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="border-b border-slate-200 bg-slate-50 font-medium text-slate-700">
                <tr>
                  <th className="px-3.5 py-2.5">Column</th>
                  <th className="px-3.5 py-2.5">Unique Count</th>
                  <th className="px-3.5 py-2.5">Top Value</th>
                  <th className="px-3.5 py-2.5">Top Frequency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white text-xs">
                {catColumns.map((col) => {
                  const s = catSummary[col] ?? {};
                  return (
                    <tr className="hover:bg-slate-50" key={col}>
                      <td className="px-3.5 py-2 font-semibold text-slate-900">{col}</td>
                      <td className="px-3.5 py-2 font-mono">{formatNumber(Number(s.unique), 0)}</td>
                      <td className="px-3.5 py-2 font-medium text-slate-800">{String(s.top ?? "N/A")}</td>
                      <td className="px-3.5 py-2 font-mono text-slate-600">{formatNumber(Number(s.freq), 0)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Missing Values Detail (if any) */}
      {missing?.by_column && missing.by_column.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-700">
            Missing Values by Column
          </h4>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {missing.by_column.map((m) => (
              <div className="flex items-center justify-between rounded-md border border-amber-200 bg-amber-50/60 p-2.5 text-xs" key={m.column}>
                <span className="font-semibold text-amber-950">{m.column}</span>
                <span className="font-mono text-amber-800">
                  {formatNumber(m.missing_count, 0)} ({formatPercent(m.missing_percent)})
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function QualityToolView({ data }: { data: QualityData }) {
  const missing = data.missingness ?? [];
  const duplicates = data.duplicate_rows;
  const constants = data.constant_columns ?? [];
  const highCard = data.high_cardinality_columns ?? [];
  const outliers = data.numeric_outliers ?? [];
  const suspicious = data.suspicious_values ?? {};

  const totalIssues =
    missing.length +
    (duplicates?.count ? 1 : 0) +
    constants.length +
    highCard.length +
    outliers.length +
    (suspicious.empty_strings?.length ?? 0) +
    (suspicious.whitespace_only_strings?.length ?? 0);

  return (
    <div className="space-y-5">
      {/* Overall Health Status Banner */}
      <div
        className={`flex items-center justify-between rounded-lg border p-4 ${
          totalIssues === 0
            ? "border-emerald-200 bg-emerald-50 text-emerald-900"
            : "border-amber-200 bg-amber-50 text-amber-950"
        }`}
      >
        <div className="flex items-center gap-3">
          <span className={`flex h-8 w-8 items-center justify-center rounded-full text-base ${
            totalIssues === 0 ? "bg-emerald-200 text-emerald-800" : "bg-amber-200 text-amber-800"
          }`}>
            {totalIssues === 0 ? "✓" : "!"}
          </span>
          <div>
            <p className="font-semibold text-sm">
              {totalIssues === 0
                ? "Dataset Health: Excellent"
                : `Detected ${totalIssues} Potential Data Quality Anomali${totalIssues === 1 ? "y" : "es"}`}
            </p>
            <p className="text-xs opacity-80">
              Scanned {formatNumber(data.row_count, 0)} rows across {formatNumber(data.column_count, 0)} columns
            </p>
          </div>
        </div>
        <Badge variant={totalIssues === 0 ? "success" : "warning"}>
          {totalIssues === 0 ? "Clean Data" : `${totalIssues} issues`}
        </Badge>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Missing Values Card */}
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
              Missing Values
            </h4>
            <Badge variant={missing.length > 0 ? "warning" : "success"}>
              {missing.length === 0 ? "None" : `${missing.length} cols`}
            </Badge>
          </div>
          {missing.length === 0 ? (
            <p className="mt-3 text-xs text-slate-500">No missing or null cells detected.</p>
          ) : (
            <div className="mt-3 space-y-2 max-h-48 overflow-y-auto pr-1">
              {missing.map((m) => (
                <div className="flex items-center justify-between text-xs" key={m.column}>
                  <span className="font-medium text-slate-800">{m.column}</span>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-16 overflow-hidden rounded bg-slate-100">
                      <div
                        className="h-full bg-amber-500"
                        style={{ width: `${Math.min(m.missing_percent, 100)}%` }}
                      />
                    </div>
                    <span className="font-mono text-slate-600">{formatPercent(m.missing_percent)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Duplicates & Constant Columns */}
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
              Duplicates & Invariants
            </h4>
            <Badge variant={duplicates?.count || constants.length > 0 ? "warning" : "success"}>
              {duplicates?.count || constants.length > 0 ? "Issues" : "Clean"}
            </Badge>
          </div>
          <div className="mt-3 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Duplicate rows:</span>
              <span className="font-semibold text-slate-900">
                {duplicates?.count ? `${duplicates.count} (${formatPercent(duplicates.percent)})` : "0"}
              </span>
            </div>
            <div className="flex items-start justify-between">
              <span className="text-slate-600">Constant columns (0 variance):</span>
              <span className="font-semibold text-slate-900">
                {constants.length === 0 ? (
                  "None"
                ) : (
                  <span className="text-amber-700">
                    {constants.map((c) => `${c.column} (${String(c.value)})`).join(", ")}
                  </span>
                )}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Numeric Outliers */}
      {outliers.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
            Numeric Outliers (IQR Method)
          </h4>
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="border-b border-slate-200 bg-slate-50 font-medium text-slate-700">
                <tr>
                  <th className="px-3.5 py-2.5">Column</th>
                  <th className="px-3.5 py-2.5">Outlier Count</th>
                  <th className="px-3.5 py-2.5">Lower Bound</th>
                  <th className="px-3.5 py-2.5">Upper Bound</th>
                  <th className="px-3.5 py-2.5">Sample Outliers</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white font-mono text-[11px]">
                {outliers.map((o) => (
                  <tr className="hover:bg-slate-50" key={o.column}>
                    <td className="px-3.5 py-2 font-sans font-semibold text-slate-900">{o.column}</td>
                    <td className="px-3.5 py-2 font-bold text-amber-700">{o.outlier_count ?? 0}</td>
                    <td className="px-3.5 py-2">{formatNumber(o.lower_bound)}</td>
                    <td className="px-3.5 py-2">{formatNumber(o.upper_bound)}</td>
                    <td className="px-3.5 py-2 font-sans text-slate-500">
                      {o.sample_outliers && o.sample_outliers.length > 0
                        ? o.sample_outliers.slice(0, 3).map((v) => formatNumber(v)).join(", ")
                        : "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Suspicious Values */}
      {((suspicious.empty_strings?.length ?? 0) > 0 || (suspicious.whitespace_only_strings?.length ?? 0) > 0) ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-3.5 text-xs text-amber-950">
          <p className="font-semibold">Suspicious Text Values:</p>
          <ul className="mt-1 list-inside list-disc space-y-1">
            {suspicious.empty_strings?.map((s) => (
              <li key={`empty-${s.column}`}>
                Column <span className="font-semibold">{s.column}</span> has {s.count} empty string(s) (&quot;&quot;)
              </li>
            ))}
            {suspicious.whitespace_only_strings?.map((s) => (
              <li key={`ws-${s.column}`}>
                Column <span className="font-semibold">{s.column}</span> has {s.count} whitespace-only value(s)
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function ColumnToolView({ data }: { data: ColumnData }) {
  const results = data.results ?? [];
  const [activeColIndex, setActiveColIndex] = useState(0);

  if (results.length === 0) {
    return <p className="text-xs text-slate-500">No column analysis results available.</p>;
  }

  const currentCol = results[activeColIndex] || results[0];

  return (
    <div className="space-y-4">
      {/* Column Selector Tabs */}
      <div className="flex flex-wrap gap-1.5 border-b border-slate-200 pb-2">
        {results.map((res, index) => (
          <button
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
              index === activeColIndex
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
            key={res.column}
            onClick={() => setActiveColIndex(index)}
            type="button"
          >
            {res.column}
            <span className="ml-1.5 text-[10px] opacity-75">({res.inferred_type})</span>
          </button>
        ))}
      </div>

      {/* Selected Column Detail View */}
      <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-950">{currentCol.column}</h4>
            <p className="text-xs text-slate-500">
              Type: <span className="font-mono">{currentCol.dtype}</span> · Inferred: {currentCol.inferred_type}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="info">
              {formatNumber(currentCol.unique_count, 0)} distinct values
            </Badge>
            <Badge variant={currentCol.missing_count > 0 ? "warning" : "success"}>
              {currentCol.missing_count} nulls ({formatPercent(currentCol.missing_percent)})
            </Badge>
          </div>
        </div>

        {/* Numeric Details */}
        {currentCol.inferred_type === "numeric" && currentCol.quantiles ? (
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Quantile Distribution
            </p>
            <div className="grid grid-cols-4 gap-2 font-mono text-xs sm:grid-cols-7">
              {Object.entries(currentCol.quantiles).map(([q, val]) => (
                <div className="rounded border border-slate-100 bg-slate-50 p-2 text-center" key={q}>
                  <div className="text-[10px] font-sans text-slate-400 uppercase">{q}</div>
                  <div className="mt-1 font-bold text-slate-900">{formatNumber(val)}</div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
              <div className="rounded bg-slate-50 p-2.5">
                <span className="text-slate-500">Skewness:</span>{" "}
                <span className="font-mono font-semibold text-slate-900">{formatNumber(currentCol.skew)}</span>
              </div>
              <div className="rounded bg-slate-50 p-2.5">
                <span className="text-slate-500">Kurtosis:</span>{" "}
                <span className="font-mono font-semibold text-slate-900">{formatNumber(currentCol.kurtosis)}</span>
              </div>
              <div className="rounded bg-slate-50 p-2.5">
                <span className="text-slate-500">Outliers:</span>{" "}
                <span className="font-mono font-semibold text-amber-700">{currentCol.outliers?.count ?? 0}</span>
              </div>
              <div className="rounded bg-slate-50 p-2.5">
                <span className="text-slate-500">Cardinality Ratio:</span>{" "}
                <span className="font-mono font-semibold text-slate-900">{formatNumber(currentCol.cardinality_ratio, 3)}</span>
              </div>
            </div>
          </div>
        ) : null}

        {/* Categorical Top Values */}
        {currentCol.top_values && currentCol.top_values.length > 0 ? (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Top Categories / Frequencies
            </p>
            <div className="space-y-1.5">
              {currentCol.top_values.map((item, idx) => (
                <div className="flex items-center justify-between text-xs" key={idx}>
                  <span className="w-1/3 truncate font-medium text-slate-800" title={item.value}>
                    {item.value}
                  </span>
                  <div className="flex w-2/3 items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded bg-slate-100">
                      <div className="h-full bg-blue-600" style={{ width: `${Math.min(item.percent, 100)}%` }} />
                    </div>
                    <span className="w-12 text-right font-mono text-slate-600">{formatPercent(item.percent)}</span>
                    <span className="w-12 text-right font-mono text-slate-400">({item.count})</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function RelationshipsToolView({ data }: { data: RelationshipData }) {
  const topPairs = data.correlations?.top_pairs ?? [];
  const matrix = data.correlations?.matrix ?? {};
  const matrixCols = Object.keys(matrix);
  const groupedStats = data.grouped_statistics ?? [];

  return (
    <div className="space-y-5">
      {/* Top Correlated Pairs */}
      {topPairs.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Strongest Linear Correlations
          </h4>
          <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
            {topPairs.map((pair, index) => {
              const r = pair.pearson_r;
              const isPositive = r >= 0;
              const strength = Math.abs(r) >= 0.7 ? "Strong" : Math.abs(r) >= 0.3 ? "Moderate" : "Weak";
              return (
                <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs shadow-2xs" key={index}>
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-semibold text-slate-900">{pair.left}</span>
                    <span className="text-slate-400">↔</span>
                    <span className="font-semibold text-slate-900">{pair.right}</span>
                  </div>
                  <div className="mt-2 flex items-center justify-between pt-1">
                    <Badge variant={Math.abs(r) >= 0.7 ? (isPositive ? "success" : "danger") : "info"}>
                      r = {formatNumber(r, 3)}
                    </Badge>
                    <span className="text-[11px] text-slate-500">{strength} correlation</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* Correlation Matrix Table */}
      {matrixCols.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Correlation Matrix
          </h4>
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-center text-xs">
              <thead className="border-b border-slate-200 bg-slate-50 font-medium text-slate-700">
                <tr>
                  <th className="px-3 py-2 text-left">Variable</th>
                  {matrixCols.map((c) => (
                    <th className="px-3 py-2" key={c}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white font-mono text-[11px]">
                {matrixCols.map((row) => (
                  <tr className="hover:bg-slate-50" key={row}>
                    <td className="px-3 py-2 text-left font-sans font-semibold text-slate-900">{row}</td>
                    {matrixCols.map((col) => {
                      const val = matrix[row]?.[col];
                      const isSelf = row === col;
                      return (
                        <td
                          className={`px-3 py-2 ${
                            isSelf ? "font-bold text-slate-400" : val !== undefined && Math.abs(val) > 0.5 ? "font-bold text-blue-700 bg-blue-50/50" : "text-slate-700"
                          }`}
                          key={col}
                        >
                          {formatNumber(val, 2)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Grouped Statistics */}
      {groupedStats.length > 0 ? (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Grouped Relationships by Category
          </h4>
          <div className="grid gap-3 sm:grid-cols-2">
            {groupedStats.map((stat, idx) => (
              <div className="rounded-lg border border-slate-200 bg-white p-3.5 text-xs shadow-2xs" key={idx}>
                <p className="font-semibold text-slate-900">
                  {stat.numeric_column} grouped by <span className="text-blue-600">{stat.category_column}</span>
                </p>
                <div className="mt-2 space-y-1.5 font-mono text-[11px]">
                  {stat.groups.map((g, gIdx) => (
                    <div className="flex items-center justify-between rounded bg-slate-50 px-2.5 py-1" key={gIdx}>
                      <span className="font-sans font-medium text-slate-800">{g.category}</span>
                      <span className="text-slate-600">
                        Mean: <span className="font-bold text-slate-900">{formatNumber(g.mean)}</span> · n={g.count}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function AgentInterpretationView({ data }: { data: AgentData }) {
  const interp = data.interpretation;
  if (!interp) return null;

  return (
    <div className="rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50/70 to-indigo-50/40 p-4 text-slate-900">
      <div className="flex items-center gap-2 text-blue-700">
        <span className="text-base">✦</span>
        <h4 className="text-xs font-semibold uppercase tracking-wider">AI Analysis Interpretation</h4>
      </div>

      <p className="mt-2 text-sm leading-relaxed font-medium text-slate-950">
        {interp.answer}
      </p>

      {interp.key_findings && interp.key_findings.length > 0 ? (
        <div className="mt-3 space-y-1.5 border-t border-blue-100 pt-3">
          <p className="text-xs font-semibold text-slate-800">Key Findings:</p>
          <ul className="list-inside list-disc space-y-1 text-xs text-slate-700">
            {interp.key_findings.map((finding, idx) => (
              <li key={idx} className="leading-5">{finding}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {interp.follow_up_questions && interp.follow_up_questions.length > 0 ? (
        <div className="mt-3 flex flex-wrap items-center gap-1.5 pt-1 text-xs">
          <span className="font-medium text-slate-600">Suggested explorations:</span>
          {interp.follow_up_questions.map((q, idx) => (
            <span className="rounded-full bg-white/80 px-2.5 py-0.5 text-blue-700 shadow-2xs" key={idx}>
              {q}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function ToolResponseViewer({
  toolName,
  data,
}: {
  toolName: string;
  data: Record<string, unknown>;
}) {
  if (toolName === "high_level") {
    return <HighLevelToolView data={data as HighLevelData} />;
  }
  if (toolName === "quality") {
    return <QualityToolView data={data as QualityData} />;
  }
  if (toolName === "column") {
    return <ColumnToolView data={data as ColumnData} />;
  }
  if (toolName === "relationships") {
    return <RelationshipsToolView data={data as RelationshipData} />;
  }
  return (
    <p className="rounded-md bg-slate-50 p-3 text-sm text-slate-600">
      Results for <span className="font-medium">{toolName}</span> are available.
      Open the plots section below for any generated charts.
    </p>
  );
}
