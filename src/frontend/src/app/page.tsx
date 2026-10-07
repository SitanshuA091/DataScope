"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/login");
  }, [router]);

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50">
      <p className="text-sm text-slate-600">Loading DataScope...</p>
    </main>
  );
}
