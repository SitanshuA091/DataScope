"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { AuthenticatedImage } from "@/components/analysis/authenticated-image";
import { Badge } from "@/components/ui/badge";
import {
  artifactCaption,
  artifactColumns,
  artifactKind,
  resolveArtifactUrl,
} from "@/lib/artifact-url";
import type { ArtifactItem } from "@/types/analysis";

function Svg({
  className = "h-4 w-4",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      {children}
    </svg>
  );
}

export function ChartGallery({ artifacts }: { artifacts: ArtifactItem[] }) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  const viewable = (artifacts ?? []).filter(
    (artifact) => resolveArtifactUrl(artifact) != null,
  );
  const total = viewable.length;

  const close = useCallback(() => setSelectedIndex(null), []);
  const step = useCallback(
    (delta: number) => {
      setSelectedIndex((current) =>
        current === null || total === 0
          ? current
          : (current + delta + total) % total,
      );
    },
    [total],
  );

  useEffect(() => {
    if (selectedIndex === null) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") close();
      if (event.key === "ArrowRight") step(1);
      if (event.key === "ArrowLeft") step(-1);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedIndex, close, step]);

  if (total === 0) {
    return null;
  }

  const selected = selectedIndex !== null ? (viewable[selectedIndex] ?? null) : null;
  const modalUrl = selected ? resolveArtifactUrl(selected) : null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-slate-900">
            Visualizations
          </h3>
          <Badge variant="info">{total}</Badge>
        </div>
        <span className="hidden text-xs text-slate-500 sm:inline">
          Click a chart to enlarge
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {viewable.map((artifact, index) => {
          const url = resolveArtifactUrl(artifact)!;
          const title = artifactCaption(artifact);
          const kind = artifactKind(artifact);
          const columns = artifactColumns(artifact);

          return (
            <div
              className="card-lift group fade-up cursor-pointer overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-500"
              key={artifact.id || `${title}-${index}`}
              onClick={() => setSelectedIndex(index)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setSelectedIndex(index);
                }
              }}
              role="button"
              style={{ animationDelay: `${Math.min(index, 8) * 50}ms` }}
              tabIndex={0}
            >
              <div className="relative p-2.5 pb-0">
                <div className="flex aspect-video w-full items-center justify-center overflow-hidden rounded-lg bg-[#ffffff] ring-1 ring-slate-200">
                  <AuthenticatedImage
                    alt={title}
                    className="max-h-full max-w-full object-contain"
                    src={url}
                  />
                </div>
                <span className="absolute right-4 top-4 grid h-7 w-7 place-items-center rounded-full bg-slate-900/70 text-white opacity-0 backdrop-blur transition group-hover:opacity-100">
                  <Svg className="h-3.5 w-3.5">
                    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
                  </Svg>
                </span>
              </div>

              <div className="px-3.5 py-3">
                <div className="flex items-start justify-between gap-2">
                  <p
                    className="truncate text-sm font-semibold capitalize text-slate-900"
                    title={title}
                  >
                    {title}
                  </p>
                  <Badge variant="info">{kind}</Badge>
                </div>
                {columns.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {columns.slice(0, 3).map((column) => (
                      <span
                        className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600"
                        key={column}
                      >
                        {column}
                      </span>
                    ))}
                    {columns.length > 3 ? (
                      <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500">
                        +{columns.length - 3}
                      </span>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>

      {selected && modalUrl && selectedIndex !== null ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm"
          onClick={close}
        >
          <div
            className="fade-up relative flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-3.5">
              <div className="min-w-0">
                <h4 className="truncate text-base font-semibold capitalize text-slate-950">
                  {artifactCaption(selected)}
                </h4>
                <div className="mt-1 flex flex-wrap items-center gap-1.5">
                  <Badge variant="info">{artifactKind(selected)}</Badge>
                  {artifactColumns(selected).map((column) => (
                    <span
                      className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600"
                      key={column}
                    >
                      {column}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span className="text-xs text-slate-500">
                  {selectedIndex + 1} / {total}
                </span>
                <button
                  aria-label="Close"
                  className="grid h-9 w-9 place-items-center rounded-lg border border-slate-300 text-slate-700 transition hover:bg-slate-100"
                  onClick={close}
                  type="button"
                >
                  <Svg className="h-4 w-4">
                    <path d="M18 6 6 18M6 6l12 12" />
                  </Svg>
                </button>
              </div>
            </div>

            <div className="relative flex min-h-0 flex-1 items-center justify-center overflow-auto bg-slate-100 p-5">
              <div className="rounded-xl bg-[#ffffff] p-3 shadow-sm ring-1 ring-slate-200">
                <AuthenticatedImage
                  alt={artifactCaption(selected)}
                  className="max-h-[70vh] max-w-full object-contain"
                  src={modalUrl}
                />
              </div>

              {total > 1 ? (
                <>
                  <button
                    aria-label="Previous chart"
                    className="absolute left-4 top-1/2 grid h-10 w-10 -translate-y-1/2 place-items-center rounded-full border border-slate-300 bg-white/90 text-slate-800 shadow-md backdrop-blur transition hover:scale-105"
                    onClick={() => step(-1)}
                    type="button"
                  >
                    <Svg className="h-5 w-5">
                      <path d="m15 18-6-6 6-6" />
                    </Svg>
                  </button>
                  <button
                    aria-label="Next chart"
                    className="absolute right-4 top-1/2 grid h-10 w-10 -translate-y-1/2 place-items-center rounded-full border border-slate-300 bg-white/90 text-slate-800 shadow-md backdrop-blur transition hover:scale-105"
                    onClick={() => step(1)}
                    type="button"
                  >
                    <Svg className="h-5 w-5">
                      <path d="m9 18 6-6-6-6" />
                    </Svg>
                  </button>
                </>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}