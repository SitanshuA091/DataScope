import { Badge } from "@/components/ui/badge";
import { formatBytes } from "@/lib/formatters";
import type { DatasetListItem } from "@/types/dataset";

export function DatasetOverview({ item }: { item: DatasetListItem | null }) {
  if (!item?.current_version) {
    return (
      <section className="border-b border-slate-200 bg-white px-5 py-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-950">
              Dataset overview
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Upload a CSV to see row counts, columns, inferred types, and
              readiness.
            </p>
          </div>
          <Badge variant="neutral">Awaiting upload</Badge>
        </div>
      </section>
    );
  }

  const version = item.current_version;

  return (
    <section className="border-b border-slate-200 bg-white px-5 py-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-base font-semibold text-slate-950">
              {item.dataset.name}
            </h2>
            <Badge
              variant={
                version.validation_status === "valid" ? "success" : "warning"
              }
            >
              {version.validation_status}
            </Badge>
          </div>
          <p className="mt-2 text-sm text-slate-600">
            {version.row_count.toLocaleString()} rows |{" "}
            {version.column_count.toLocaleString()} columns | CSV |{" "}
            {formatBytes(version.file_size)}
          </p>
          {version.validation_error ? (
            <p className="mt-3 text-sm text-red-600">
              {version.validation_error}
            </p>
          ) : null}
        </div>

        <div className="grid grid-cols-3 gap-2 text-sm">
          <div className="rounded-md bg-slate-50 px-3 py-2">
            <p className="text-xs text-slate-500">Rows</p>
            <p className="font-semibold text-slate-950">
              {version.row_count.toLocaleString()}
            </p>
          </div>
          <div className="rounded-md bg-slate-50 px-3 py-2">
            <p className="text-xs text-slate-500">Columns</p>
            <p className="font-semibold text-slate-950">
              {version.column_count.toLocaleString()}
            </p>
          </div>
          <div className="rounded-md bg-slate-50 px-3 py-2">
            <p className="text-xs text-slate-500">Version</p>
            <p className="font-semibold text-slate-950">
              {version.version_number}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
