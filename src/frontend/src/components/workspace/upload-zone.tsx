"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api-client";
import { USE_MOCKS } from "@/lib/constants";
import type { DatasetUploadResponse } from "@/types/dataset";

export function UploadZone({
  workspaceId,
  onUploaded,
}: {
  workspaceId: string;
  onUploaded: () => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  async function upload(file: File | null | undefined) {
    if (!file) {
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setIsUploading(true);
    setError(null);

    try {
      if (USE_MOCKS) {
        await new Promise((resolve) => window.setTimeout(resolve, 500));
        setFileName(file.name);
      } else {
        await apiFetch<DatasetUploadResponse>(
          `/workspaces/${workspaceId}/datasets`,
          {
            method: "POST",
            body: formData,
          },
        );
      }
      onUploaded();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Upload failed.",
      );
    } finally {
      setIsUploading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-950">Upload CSV</h2>
          <p className="mt-1 text-sm text-slate-600">
            Add a dataset to inspect schema details and run analyses.
          </p>
          {fileName ? (
            <p className="mt-2 text-xs font-medium text-emerald-700">
              Staged locally: {fileName}
            </p>
          ) : null}
        </div>
        <input
          accept=".csv,text/csv"
          className="hidden"
          onChange={(event) => upload(event.target.files?.[0])}
          ref={inputRef}
          type="file"
        />
        <Button
          disabled={isUploading}
          onClick={() => inputRef.current?.click()}
        >
          {isUploading ? "Uploading..." : "Choose CSV"}
        </Button>
      </div>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
