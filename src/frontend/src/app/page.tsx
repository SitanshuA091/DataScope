"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";

export default function Home() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) {
      return;
    }

    router.replace(user ? "/workspaces" : "/login");
  }, [isLoading, router, user]);

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50">
      <p className="text-sm text-slate-600">Loading DataScope...</p>
    </main>
  );
}
