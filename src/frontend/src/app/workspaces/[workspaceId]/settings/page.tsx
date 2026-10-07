"use client";

import { use, useState } from "react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api-client";
import type { Workspace } from "@/types/workspace";

export default function WorkspaceSettingsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = use(params);
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function rename(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setMessage(null);

    try {
      const workspace = await apiFetch<Workspace>(
        `/workspaces/${workspaceId}`,
        {
          method: "PATCH",
          body: { title },
        },
      );
      setTitle(workspace.title);
      setMessage("Workspace renamed.");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to rename workspace.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function scheduleDelete() {
    setError(null);
    setMessage(null);

    try {
      await apiFetch<void>(`/workspaces/${workspaceId}`, {
        method: "DELETE",
      });
      setMessage("Workspace deletion scheduled.");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to delete workspace.",
      );
    }
  }

  return (
    <WorkspaceShell>
      <div className="mx-auto max-w-3xl px-5 py-6">
        <h1 className="text-2xl font-semibold tracking-normal">
          Workspace settings
        </h1>
        <Card className="mt-6 p-5">
          <form onSubmit={rename}>
            <label
              className="text-sm font-medium text-slate-700"
              htmlFor="workspace-title"
            >
              Workspace name
            </label>
            <input
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              id="workspace-title"
              onChange={(event) => setTitle(event.target.value)}
              placeholder="New workspace name"
              value={title}
            />
            <div className="mt-4 flex justify-end">
              <Button disabled={isSaving || !title.trim()} type="submit">
                Save
              </Button>
            </div>
          </form>
        </Card>

        <Card className="mt-4 p-5">
          <h2 className="text-base font-semibold text-slate-950">
            Delete workspace
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            This schedules deletion using the backend retention flow.
          </p>
          <div className="mt-4">
            <Button onClick={scheduleDelete} variant="danger">
              Delete
            </Button>
          </div>
        </Card>

        {message ? <p className="mt-4 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      </div>
    </WorkspaceShell>
  );
}
