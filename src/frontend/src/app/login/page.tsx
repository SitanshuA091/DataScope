"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

export default function LoginPage() {
  const router = useRouter();
  const { user, isLoading, error, loginWithGoogle } = useAuth();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/workspaces");
    }
  }, [isLoading, router, user]);

  return (
    <main className="grid min-h-screen bg-slate-950 text-white lg:grid-cols-[1fr_420px]">
      <section className="flex min-h-[46vh] flex-col justify-between bg-[linear-gradient(135deg,#0f172a_0%,#1e3a8a_48%,#0f766e_100%)] px-6 py-8 lg:min-h-screen lg:px-12">
        <div className="text-lg font-semibold">DataScope</div>
        <div className="max-w-3xl pb-8">
          <p className="text-sm font-medium uppercase tracking-wide text-cyan-100">
            Dataset analysis workspace
          </p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-normal sm:text-5xl">
            Turn uploaded CSVs into reusable analysis records.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-blue-50">
            Sign in with Google to manage workspaces, upload datasets, inspect
            schema quality, and run guided analysis jobs.
          </p>
        </div>
      </section>
      <section className="flex items-center bg-white px-6 py-10 text-slate-950 lg:px-10">
        <div className="w-full">
          <h2 className="text-2xl font-semibold">Sign in</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Your backend session is created by the FastAPI Google OAuth flow.
          </p>
          <Button
            className="mt-8 w-full"
            disabled={isLoading}
            onClick={loginWithGoogle}
          >
            Continue with Google
          </Button>
          {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
        </div>
      </section>
    </main>
  );
}
