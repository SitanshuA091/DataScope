"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppLogo } from "@/components/ui/app-logo";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useAuth } from "@/hooks/use-auth";

function GoogleIcon() {
  return (
    <svg aria-hidden="true" className="h-5 w-5" viewBox="0 0 24 24">
      <path
        d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.46a5.52 5.52 0 0 1-2.4 3.62v3h3.88c2.27-2.09 3.58-5.17 3.58-8.81z"
        fill="#4285F4"
      />
      <path
        d="M12 24c3.24 0 5.96-1.07 7.94-2.91l-3.88-3a7.2 7.2 0 0 1-10.7-3.77H1.34v3.09A12 12 0 0 0 12 24z"
        fill="#34A853"
      />
      <path
        d="M5.36 14.32a7.2 7.2 0 0 1 0-4.64V6.59H1.34a12 12 0 0 0 0 10.82l4.02-3.09z"
        fill="#FBBC05"
      />
      <path
        d="M12 4.75c1.76 0 3.34.61 4.58 1.8l3.44-3.44A11.5 11.5 0 0 0 12 0 12 12 0 0 0 1.34 6.59l4.02 3.09A7.15 7.15 0 0 1 12 4.75z"
        fill="#EA4335"
      />
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const { user, isLoading, error, loginWithGoogle } = useAuth();

  useEffect(() => {
    if (!isLoading && user) router.replace("/workspaces");
  }, [isLoading, router, user]);

  return (
    <main className="flex min-h-screen flex-col px-6 py-7">
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden">
        <svg
          className="absolute left-1/2 top-1/2 h-[min(82vh,720px)] w-[min(100vw,1200px)] -translate-x-1/2 -translate-y-1/2 text-slate-600 opacity-[0.38] dark:text-slate-700 dark:opacity-[0.44]"
          fill="none"
          viewBox="0 0 1000 560"
        >
          <g stroke="currentColor" strokeDasharray="4 8" strokeWidth="1.5">
            <path d="M80 100H920M80 190H920M80 280H920M80 370H920M80 460H920" />
            <path d="M180 70V480M340 70V480M500 70V480M660 70V480M820 70V480" />
          </g>
          <g stroke="currentColor" strokeWidth="2.5">
            <path d="M130 410L270 350L390 375L530 255L650 292L790 160L870 185" />
            <path d="M130 465V430M170 465V400M210 465V420M250 465V380M290 465V415M330 465V390" opacity="0.6" />
            <circle cx="270" cy="350" r="4" fill="var(--background)" />
            <circle cx="530" cy="255" r="4" fill="var(--background)" />
            <circle cx="790" cy="160" r="4" fill="var(--background)" />
          </g>
        </svg>
      </div>
      <header className="mx-auto flex w-full max-w-4xl items-center justify-between">
        <div className="flex items-center gap-2.5">
          <AppLogo className="h-8 w-8" />
          <span className="app-brand text-xl font-semibold">DataScope</span>
        </div>
        <ThemeToggle />
      </header>

      <div className="relative z-10 flex flex-1 items-center justify-center py-12">
        <section className="login-sign-in-card fade-up w-full max-w-md rounded-2xl border border-slate-200/80 bg-white/35 p-8 text-center shadow-lg shadow-slate-900/5 backdrop-blur-sm dark:border-white/10 dark:bg-white/[0.045] dark:shadow-black/10 sm:p-10">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
            Data analysis workspace
          </p>
          <h1 className="mt-3 text-sm font-normal text-foreground">
            Sign in to DataScope
          </h1>
          <p className="mt-2 text-lg font-bold leading-7 text-foreground">
            Turn your CSVs into reusable analysis records with AI.
          </p>
          <p className="mt-3 text-xs text-slate-500">
            CSV upload <span aria-hidden="true">·</span> Guided analysis{" "}
            <span aria-hidden="true">·</span> Saved results
          </p>

          <Button
            className="login-sign-in-button mt-7 h-11 w-full rounded-xl text-sm"
            disabled={isLoading}
            onClick={loginWithGoogle}
            variant="secondary"
          >
            <GoogleIcon />
            {isLoading ? "Checking session…" : "Continue with Google"}
          </Button>

          {error ? (
            <p
              role="alert"
              className="mt-4 rounded-lg border border-red-200 bg-red-50/60 px-3 py-2 text-sm text-red-600 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
            >
              {error}
            </p>
          ) : null}
        </section>
      </div>

      <p className="text-center text-xs text-slate-500">
        Your datasets stay private to your account.
      </p>
    </main>
  );
}
