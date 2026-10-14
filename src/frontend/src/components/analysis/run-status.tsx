import { Badge } from "@/components/ui/badge";

export function RunStatus({
  status,
  progress,
  stage,
}: {
  status: string;
  progress?: number | null;
  stage?: string | null;
}) {
  const variant =
    status === "completed"
      ? "success"
      : status === "failed" || status === "cancelled"
        ? "danger"
        : status === "running"
          ? "info"
          : "warning";

  const showProgress =
    typeof progress === "number" &&
    (status === "pending" || status === "running");

  return (
    <div className="flex flex-col items-end gap-1.5">
      <div className="flex items-center gap-3">
        <Badge variant={variant}>{status}</Badge>
        {showProgress ? (
          <div className="h-2 w-28 overflow-hidden rounded bg-slate-100">
            <div
              className="h-full bg-blue-600 transition-[width]"
              style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
            />
          </div>
        ) : null}
      </div>
      {stage && (status === "pending" || status === "running") ? (
        <p className="text-xs capitalize text-slate-500">
          {stage.replaceAll("_", " ")}
          {showProgress ? ` · ${Math.round(progress)}%` : ""}
        </p>
      ) : null}
    </div>
  );
}
