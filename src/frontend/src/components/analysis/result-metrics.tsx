export function ResultMetrics({
  results,
}: {
  results: Record<string, unknown> | null;
}) {
  if (!results) {
    return <p className="text-sm text-slate-600">No results available yet.</p>;
  }

  const entries = Object.entries(results).slice(0, 6);

  return (
    <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {entries.map(([key, value]) => (
        <div className="rounded-md bg-slate-50 p-3" key={key}>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {key.replaceAll("_", " ")}
          </dt>
          <dd className="mt-1 truncate text-sm font-semibold text-slate-950">
            {typeof value === "object" && value !== null
              ? JSON.stringify(value)
              : String(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}
