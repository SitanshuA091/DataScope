"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { USE_MOCKS } from "@/lib/constants";
import { useWorkspaces } from "@/hooks/use-workspaces";

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { workspaces, createWorkspace, isLoading } = useWorkspaces();

  async function handleCreate() {
    const workspace = await createWorkspace("Untitled workspace");
    router.push(`/workspaces/${workspace.id}`);
  }

  return (
    <aside className="w-full border-b border-slate-200 bg-white md:w-64 md:shrink-0 md:border-b-0 md:border-r">
      <div className="flex items-center justify-between gap-3 px-4 py-4 md:block">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Workspaces
        </p>
        {USE_MOCKS ? (
          <p className="mt-1 hidden text-xs text-slate-500 md:block">
            Local preview data
          </p>
        ) : null}
        <Button className="mt-0 md:mt-4 md:w-full" onClick={handleCreate}>
          New upload
        </Button>
      </div>
      <nav className="flex gap-2 overflow-x-auto px-4 pb-4 md:block md:space-y-1 md:overflow-visible">
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : workspaces.length > 0 ? (
          workspaces.map((workspace) => {
            const active = pathname === `/workspaces/${workspace.id}`;
            return (
              <Link
                className={`block min-w-44 truncate rounded-md px-3 py-2 text-sm transition md:min-w-0 ${
                  active
                    ? "bg-blue-50 font-medium text-blue-700"
                    : "text-slate-700 hover:bg-slate-100"
                }`}
                href={`/workspaces/${workspace.id}`}
                key={workspace.id}
              >
                {workspace.title}
              </Link>
            );
          })
        ) : (
          <p className="max-w-44 text-sm leading-6 text-slate-500">
            No workspaces yet.
          </p>
        )}
      </nav>
    </aside>
  );
}
