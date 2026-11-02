"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { UserAvatar } from "@/components/ui/user-avatar";
import { useAuth } from "@/hooks/use-auth";

export function Topbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6">
      <Link className="flex items-center gap-2" href="/workspaces">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img alt="" className="h-7 w-7" src="/favicon.ico" />
        <span className="app-brand text-xl font-semibold tracking-normal">
          DataScope
        </span>
      </Link>
      <div className="flex min-w-0 items-center gap-3">
        <UserAvatar
          avatarUrl={user?.avatar_url}
          className="h-9 w-9"
          email={user?.email}
          name={user?.name}
        />
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