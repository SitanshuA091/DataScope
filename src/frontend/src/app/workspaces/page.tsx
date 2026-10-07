"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { useWorkspaces } from "@/hooks/use-workspaces";
import { formatDateTime } from "@/lib/formatters";

export default function WorkspacesPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const { workspaces, isLoading, error, createWorkspace } = useWorkspaces();

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
    }
  }, [isAuthLoading, router, user]);

  async function handleCreate() {
    const workspace = await createWorkspace("Untitled workspace");
    router.push(`/workspaces/${workspace.id}`);
  }

  if (!isAuthLoading && !user) {
    return null;
  }

  return (
    <WorkspaceShell>
      <div className="mx-auto max-w-6xl px-5 py-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">
              Workspaces
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Pick up a dataset analysis or start a fresh upload.
            </p>
          </div>
          <Button onClick={handleCreate}>Create workspace</Button>
        </div>

        {error ? <p className="mt-6 text-sm text-red-600">{error}</p> : null}

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {isLoading
            ? Array.from({ length: 3 }).map((_, index) => (
                <Card className="h-36 animate-pulse bg-white p-5" key={index}>
                  <div className="h-5 w-2/3 rounded bg-slate-200" />
                  <div className="mt-4 h-4 w-1/2 rounded bg-slate-100" />
                </Card>
              ))
            : workspaces.map((workspace) => (
                <Link href={`/workspaces/${workspace.id}`} key={workspace.id}>
                  <Card className="h-full p-5 transition hover:border-blue-300 hover:shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <h2 className="truncate text-base font-semibold text-slate-950">
                        {workspace.title}
                      </h2>
                      <span className="rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                        CSV
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      Last activity {formatDateTime(workspace.last_activity_at)}
                    </p>
                    <p className="mt-5 text-sm font-medium text-blue-700">
                      Open workspace
                    </p>
                  </Card>
                </Link>
              ))}
        </div>

        {!isLoading && workspaces.length === 0 ? (
          <Card className="mt-6 p-8 text-center">
            <h2 className="text-lg font-semibold">No workspaces yet</h2>
            <p className="mt-2 text-sm text-slate-600">
              Create a workspace, then upload a CSV to begin analysis.
            </p>
          </Card>
        ) : null}
      </div>
    </WorkspaceShell>
  );
}
