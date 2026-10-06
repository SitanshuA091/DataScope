import Link from "next/link";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 px-6">
      <div className="text-center">
        <h1 className="text-3xl font-semibold text-slate-950">Not found</h1>
        <p className="mt-2 text-sm text-slate-600">
          This page does not exist.
        </p>
        <Link
          className="mt-6 inline-flex rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          href="/workspaces"
        >
          Back to workspaces
        </Link>
      </div>
    </main>
  );
}
