import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/formatters";
import type { Workspace } from "@/types/workspace";

export function WorkspaceHeader({
  workspace,
  datasetStatus,
}: {
  workspace: Workspace;
  datasetStatus: string;
}) {
  return (
    <div className="flex flex-col gap-4 border-b border-slate-200 bg-white px-5 py-5 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">
          {workspace.title}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Last activity {formatDateTime(workspace.last_activity_at)}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <Badge variant={datasetStatus === "ready" ? "success" : "neutral"}>
          {datasetStatus}
        </Badge>
        {datasetStatus === "ready" ? (
          <Link
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            href={`/workspaces/${workspace.id}/chat`}
          >
            Chat
          </Link>
        ) : (
          <span className="cursor-not-allowed rounded-md bg-slate-200 px-4 py-2 text-sm font-medium text-slate-500">
            Chat
          </span>
        )}
        <Link
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-100"
          href={`/workspaces/${workspace.id}/settings`}
        >
          Settings
        </Link>
      </div>
    </div>
  );
}