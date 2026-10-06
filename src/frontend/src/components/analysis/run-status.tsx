import { Badge } from "@/components/ui/badge";

export function RunStatus({
  status,
  progress,
}: {
  status: string;
  progress?: number | null;
}) {
  const variant =
    status === "completed"
      ? "success"
      : status === "failed" || status === "cancelled"
        ? "danger"
        : status === "running"
          ? "info"
          : "warning";

  return (
    <div className="flex items-center gap-3">
      <Badge variant={variant}>{status}</Badge>
      {typeof progress === "number" ? (
        <div className="h-2 w-28 overflow-hidden rounded bg-slate-100">
          <div
            className="h-full bg-blue-600"
            style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
          />
        </div>
      ) : null}
    </div>
  );
}
