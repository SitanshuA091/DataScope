"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppLogo } from "@/components/ui/app-logo";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useAuth } from "@/hooks/use-auth";

function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24">
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

function FeatureIcon({ children }: { children: React.ReactNode }) {
  return (
    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-white/70 text-blue-700 ring-1 ring-slate-200 dark:bg-white/5 dark:text-slate-300 dark:ring-white/10">
      <svg
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
        viewBox="0 0 24 24"
      >
        {children}
      </svg>
    </span>
  );
}

const FEATURES = [
  {
    title: "Upload a CSV",
    text: "Get an instant schema overview with rows, columns and types.",
    icon: (
      <>
        <path d="M12 16V4M7 9l5-5 5 5" />
        <path d="M5 20h14" />
      </>
    ),
  },
  {
    title: "Ask the agent",
    text: "It picks the right analysis tools and explains computed results.",
    icon: (
      <>
        <path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </>
    ),
  },
  {
    title: "Keep every result",
    text: "Runs, charts and findings are saved and reopen anytime.",
    icon: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { user, isLoading, error, loginWithGoogle } = useAuth();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/workspaces");
    }
  }, [isLoading, router, user]);

  return (
    <main className="grid min-h-screen lg:grid-cols-[1fr_480px]">
      <section className="relative flex min-h-[52vh] flex-col justify-between overflow-hidden bg-[linear-gradient(135deg,#dbeafe_0%,#eef2ff_50%,#e0f2fe_100%)] px-6 py-8 text-slate-950 lg:min-h-screen lg:px-14 dark:bg-[linear-gradient(135deg,#0b0f16_0%,#151b26_55%,#1d2532_100%)]">
        <div
          aria-hidden
          className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-blue-400/30 blur-3xl dark:bg-slate-400/10"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -bottom-24 right-0 h-80 w-80 rounded-full bg-violet-400/25 blur-3xl dark:bg-slate-500/10"
        />

        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AppLogo className="h-10 w-10" />
            <span className="app-brand text-3xl font-semibold tracking-normal">
              DataScope
            </span>
          </div>
          <ThemeToggle />
        </div>

        <div className="relative max-w-3xl py-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white/60 px-3 py-1 text-xs font-medium uppercase tracking-wide text-slate-700 backdrop-blur dark:bg-white/5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Dataset analysis workspace
          </span>
          <h1 className="mt-5 max-w-2xl text-4xl font-semibold tracking-normal sm:text-5xl">
            Turn uploaded CSVs into reusable analysis records.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-600">
            Sign in to manage workspaces, upload datasets, inspect schema
            quality, and run guided analysis jobs.
          </p>

          <div className="mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
            {FEATURES.map((feature) => (
              <div
                className="rounded-xl border border-slate-200 bg-white/60 p-4 backdrop-blur transition hover:-translate-y-0.5 hover:border-blue-300 dark:bg-white/5"
                key={feature.title}
              >
                <FeatureIcon>{feature.icon}</FeatureIcon>
                <p className="mt-3 text-sm font-semibold text-slate-900">
                  {feature.title}
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-600">
                  {feature.text}
                </p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-xs text-slate-500">
          Your datasets stay private to your account.
        </p>
      </section>

      <section className="flex items-center justify-center bg-white px-6 py-10 text-slate-950 lg:px-12">
        <div className="w-full max-w-sm">
          <h2 className="text-3xl font-semibold">Welcome back</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Sign in with your Google account to open your workspaces.
          </p>

          <Button
            className="mt-8 h-12 w-full rounded-xl text-base"
            disabled={isLoading}
            onClick={loginWithGoogle}
            variant="secondary"
          >
            <GoogleIcon />
            {isLoading ? "Checking session..." : "Continue with Google"}
          </Button>

          {error ? (
            <p className="mt-4 rounded-lg border border-red-200 bg-red-50/60 px-3 py-2 text-sm text-red-600">
              {error}
            </p>
          ) : null}

          <p className="mt-8 text-xs leading-5 text-slate-500">
            We only request your name, email and profile photo to create your
            account.
          </p>
        </div>
      </section>
    </main>
  );
}