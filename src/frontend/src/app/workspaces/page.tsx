"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { useWorkspaces } from "@/hooks/use-workspaces";
import { formatDateTime } from "@/lib/formatters";

function PlusIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

function ArrowIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function InitialTile({ title }: { title: string }) {
  const initial = title.trim().charAt(0).toUpperCase() || "W";
  return (
    <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-linear-to-br from-blue-500 to-blue-700 text-base font-semibold text-white shadow-xs">
      {initial}
    </div>
  );
}

export default function WorkspacesPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const { workspaces, isLoading, error, createWorkspace } = useWorkspaces();
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
    }
  }, [isAuthLoading, router, user]);

  const visibleWorkspaces = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return workspaces;
    return workspaces.filter((workspace) =>
      workspace.title.toLowerCase().includes(query),
    );
  }, [search, workspaces]);

  async function handleCreate() {
    if (isCreating) return;
    setIsCreating(true);
    setCreateError(null);
    try {
      const workspace = await createWorkspace("Untitled workspace");
      router.push(`/workspaces/${workspace.id}`);
    } catch (requestError) {
      setCreateError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to create workspace.",
      );
      setIsCreating(false);
    }
  }

  if (!isAuthLoading && !user) {
    return null;
  }

  const firstName = user?.name?.split(" ")[0];
  const showSearch = workspaces.length > 4;
  const isEmpty = !isLoading && workspaces.length === 0;
  const latestActivityAt = workspaces.reduce<string | null>((latest, workspace) => {
    if (!latest) return workspace.last_activity_at;
    return Date.parse(workspace.last_activity_at) > Date.parse(latest)
      ? workspace.last_activity_at
      : latest;
  }, null);

  return (
    <WorkspaceShell>
      <div className="mx-auto max-w-6xl px-5 py-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-700">
              {firstName ? `Welcome back, ${firstName}` : "Welcome back"}
            </p>
            <div className="mt-1 flex items-center gap-3">
              <h1 className="text-3xl font-semibold tracking-normal">
                Workspaces
              </h1>
            </div>
            <p className="mt-2 text-sm text-slate-600">
              Your data work, organized from the first upload to every saved result.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {showSearch ? (
              <input
                className="h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-hidden focus:ring-1 focus:ring-blue-500 sm:w-56"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search workspaces..."
                value={search}
              />
            ) : null}
            <Button disabled={isCreating} onClick={handleCreate}>
              <PlusIcon className="h-4 w-4" />
              {isCreating ? "Creating..." : "New workspace"}
            </Button>
          </div>
        </div>

        <section
          aria-label="Workspace activity overview"
          className="mt-6 grid gap-3 sm:grid-cols-2"
        >
          <Card className="flex items-center justify-between gap-4 px-5 py-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Your workspaces
              </p>
              <p className="mt-1 text-sm text-slate-600">
                Saved spaces for your datasets and analyses
              </p>
            </div>
            <span className="text-2xl font-semibold tabular-nums text-foreground">
              {isLoading ? "—" : workspaces.length}
            </span>
          </Card>
          <Card className="flex items-center justify-between gap-4 px-5 py-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Latest activity
              </p>
              <p className="mt-1 text-sm text-slate-600">
                {isLoading
                  ? "Loading your activity…"
                  : latestActivityAt
                    ? formatDateTime(latestActivityAt)
                    : "No activity yet"}
              </p>
            </div>
          </Card>
        </section>

        {error ? <p className="mt-6 text-sm text-red-600">{error}</p> : null}
        {createError ? (
          <p className="mt-6 text-sm text-red-600">{createError}</p>
        ) : null}

        {isEmpty ? (
          <Card className="mt-8 flex flex-col items-center border-dashed px-6 py-16 text-center">
            <div className="grid h-16 w-16 place-items-center rounded-2xl bg-linear-to-br from-blue-500 to-blue-700 text-white shadow-xs">
              <PlusIcon className="h-8 w-8" />
            </div>
            <h2 className="mt-5 text-xl font-semibold">No workspaces yet</h2>
            <p className="mt-2 max-w-sm text-sm text-slate-600">
              Create a workspace, then upload a CSV and ask the agent to
              investigate it.
            </p>
            <Button className="mt-6" disabled={isCreating} onClick={handleCreate}>
              <PlusIcon className="h-4 w-4" />
              Create your first workspace
            </Button>
          </Card>
        ) : (
          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {isLoading
              ? Array.from({ length: 3 }).map((_, index) => (
                  <Card className="h-40 animate-pulse p-5" key={index}>
                    <div className="h-11 w-11 rounded-xl bg-slate-200" />
                    <div className="mt-4 h-4 w-2/3 rounded bg-slate-200" />
                    <div className="mt-3 h-3 w-1/2 rounded bg-slate-100" />
                  </Card>
                ))
              : (
                  <>
                    {visibleWorkspaces.map((workspace) => (
                      <Link
                        className="group block"
                        href={`/workspaces/${workspace.id}`}
                        key={workspace.id}
                      >
                        <Card className="card-lift flex h-40 flex-col justify-between p-5">
                          <div className="flex items-start gap-3">
                            <InitialTile title={workspace.title} />
                            <div className="min-w-0 flex-1">
                              <h2 className="truncate text-base font-semibold text-slate-950">
                                {workspace.title}
                              </h2>
                              <p className="mt-1 text-xs text-slate-500">
                                Last activity{" "}
                                {formatDateTime(workspace.last_activity_at)}
                              </p>
                            </div>
                            <Badge>CSV</Badge>
                          </div>
                          <div className="flex items-center gap-1.5 text-sm font-medium text-blue-700">
                            Open workspace
                            <ArrowIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                          </div>
                        </Card>
                      </Link>
                    ))}
                    <button
                      className="card-lift group flex h-40 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 bg-white/40 text-slate-600 hover:text-blue-700 disabled:opacity-60"
                      disabled={isCreating}
                      onClick={handleCreate}
                      type="button"
                    >
                      <span className="grid h-10 w-10 place-items-center rounded-full bg-slate-100 text-slate-600 transition group-hover:bg-blue-100 group-hover:text-blue-700">
                        <PlusIcon />
                      </span>
                      <span className="text-sm font-medium">
                        {isCreating ? "Creating..." : "New workspace"}
                      </span>
                    </button>
                  </>
                )}
          </div>
        )}

        {!isLoading && search && visibleWorkspaces.length === 0 ? (
          <p className="mt-6 text-sm text-slate-500">
            No workspaces match &quot;{search}&quot;.
          </p>
        ) : null}
      </div>
    </WorkspaceShell>
  );
}
