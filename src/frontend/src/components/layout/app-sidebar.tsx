"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useWorkspaces } from "@/hooks/use-workspaces";

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { workspaces, createWorkspace, isLoading } = useWorkspaces();
  const [isCreating, setIsCreating] = useState(false);

  async function handleCreate() {
    if (isCreating) return;
    setIsCreating(true);
    try {
      const workspace = await createWorkspace("Untitled workspace");
      router.push(`/workspaces/${workspace.id}`);
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <aside className="w-full border-b border-slate-200 bg-white/70 backdrop-blur md:w-64 md:shrink-0 md:border-b-0 md:border-r">
      <div className="flex items-center justify-between gap-3 px-4 py-4 md:block">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Workspaces
        </p>
        <Button
          className="mt-0 md:mt-4 md:w-full"
          disabled={isCreating}
          onClick={handleCreate}
        >
          {isCreating ? "Creating..." : "New upload"}
        </Button>
      </div>
      <nav className="flex gap-2 overflow-x-auto px-3 pb-4 md:block md:space-y-1 md:overflow-visible">
        {isLoading ? (
          <p className="px-1 text-sm text-slate-500">Loading...</p>
        ) : workspaces.length > 0 ? (
          workspaces.map((workspace) => {
            const active = pathname.startsWith(`/workspaces/${workspace.id}`);
            return (
              <Link
                className={`flex min-w-44 items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition md:min-w-0 ${
                  active
                    ? "bg-blue-50 font-medium text-blue-700 ring-1 ring-blue-200"
                    : "text-slate-700 hover:bg-slate-100"
                }`}
                href={`/workspaces/${workspace.id}`}
                key={workspace.id}
              >
                <span
                  className={`grid h-6 w-6 shrink-0 place-items-center rounded-md text-xs font-semibold ${
                    active
                      ? "bg-blue-600 text-white"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {workspace.title.trim().charAt(0).toUpperCase() || "W"}
                </span>
                <span className="truncate">{workspace.title}</span>
              </Link>
            );
          })
        ) : (
          <p className="max-w-44 px-1 text-sm leading-6 text-slate-500">
            No workspaces yet.
          </p>
        )}
      </nav>
    </aside>
  );
}