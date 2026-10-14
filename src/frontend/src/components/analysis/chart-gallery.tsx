"use client";

import { useState } from "react";
import { AuthenticatedImage } from "@/components/analysis/authenticated-image";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  artifactCaption,
  artifactColumns,
  artifactKind,
  resolveArtifactUrl,
} from "@/lib/artifact-url";
import type { ArtifactItem } from "@/types/analysis";

export function ChartGallery({ artifacts }: { artifacts: ArtifactItem[] }) {
  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactItem | null>(
    null,
  );

  const viewable = (artifacts ?? []).filter(
    (artifact) => resolveArtifactUrl(artifact) != null,
  );

  if (viewable.length === 0) {
    return null;
  }

  const modalUrl = selectedArtifact
    ? resolveArtifactUrl(selectedArtifact)
    : null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">
          Visualizations & Plots ({viewable.length})
        </h3>
        <span className="text-xs text-slate-500">Click any chart to enlarge</span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {viewable.map((artifact, index) => {
          const url = resolveArtifactUrl(artifact)!;
          const title = artifactCaption(artifact);
          const kind = artifactKind(artifact);
          const columns = artifactColumns(artifact);

          return (
            <Card
              className="group cursor-pointer overflow-hidden transition-all hover:border-blue-300 hover:shadow-md"
              key={artifact.id || `${title}-${index}`}
              onClick={() => setSelectedArtifact(artifact)}
            >
              <div className="border-b border-slate-100 bg-slate-50/70 px-3.5 py-2.5">
                <div className="flex items-start justify-between gap-2">
                  <p
                    className="truncate text-xs font-semibold capitalize text-slate-900"
                    title={title}
                  >
                    {title}
                  </p>
                  <Badge variant="info">{kind}</Badge>
                </div>
                {columns.length > 0 ? (
                  <p className="mt-1 truncate text-[11px] text-slate-500">
                    Cols: {columns.join(", ")}
                  </p>
                ) : null}
              </div>

              <div className="relative flex aspect-video w-full items-center justify-center bg-slate-50 p-2">
                <AuthenticatedImage
                  alt={title}
                  className="max-h-full max-w-full object-contain transition group-hover:scale-[1.02]"
                  src={url}
                />
              </div>
            </Card>
          );
        })}
      </div>

      {selectedArtifact && modalUrl ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs"
          onClick={() => setSelectedArtifact(null)}
        >
          <div
            className="relative max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-5 py-3">
              <div>
                <h4 className="text-sm font-semibold capitalize text-slate-950">
                  {artifactCaption(selectedArtifact)}
                </h4>
                {artifactColumns(selectedArtifact).length > 0 ? (
                  <p className="text-xs text-slate-500">
                    Columns: {artifactColumns(selectedArtifact).join(", ")}
                  </p>
                ) : null}
              </div>
              <Button
                onClick={() => setSelectedArtifact(null)}
                size="sm"
                variant="secondary"
              >
                Close
              </Button>
            </div>
            <div className="flex max-h-[calc(90vh-4rem)] items-center justify-center overflow-auto bg-slate-900/5 p-4">
              <AuthenticatedImage
                alt={artifactCaption(selectedArtifact)}
                className="max-h-[75vh] max-w-full rounded object-contain shadow-sm"
                src={modalUrl}
              />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
