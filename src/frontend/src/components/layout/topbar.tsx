"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { USE_MOCKS } from "@/lib/constants";

export function Topbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6">
      <Link className="text-lg font-semibold tracking-normal" href="/workspaces">
        DataScope
      </Link>
      <div className="flex min-w-0 items-center gap-3">
        {USE_MOCKS ? (
          <span className="hidden rounded bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 sm:inline-flex">
            Mock API
          </span>
        ) : null}
        {user?.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            alt=""
            className="h-9 w-9 rounded-full border border-slate-200"
            src={user.avatar_url}
          />
        ) : (
          <div className="grid h-9 w-9 place-items-center rounded-full bg-slate-200 text-sm font-semibold text-slate-700">
            {(user?.name ?? user?.email ?? "U").slice(0, 1).toUpperCase()}
          </div>
        )}
        <div className="hidden min-w-0 text-right sm:block">
          <p className="truncate text-sm font-medium text-slate-900">
            {user?.name ?? "Signed in"}
          </p>
          <p className="truncate text-xs text-slate-500">{user?.email}</p>
        </div>
        <Button onClick={handleLogout} variant="secondary">
          Sign out
        </Button>
      </div>
    </header>
  );
}
