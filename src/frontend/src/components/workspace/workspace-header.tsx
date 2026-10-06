import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { USE_MOCKS } from "@/lib/constants";
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
        {USE_MOCKS ? <Badge variant="info">Preview</Badge> : null}
        <Badge variant={datasetStatus === "ready" ? "success" : "neutral"}>
          {datasetStatus}
        </Badge>
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
