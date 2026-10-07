"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api-client";

export function useDatasetActions() {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function deleteDataset(datasetId: string) {
    setIsDeleting(true);
    setError(null);

    try {
      await apiFetch<void>(`/datasets/${datasetId}`, { method: "DELETE" });
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Unable to delete dataset.";
      setError(message);
      throw requestError;
    } finally {
      setIsDeleting(false);
    }
  }

  return { deleteDataset, isDeleting, error };
}
