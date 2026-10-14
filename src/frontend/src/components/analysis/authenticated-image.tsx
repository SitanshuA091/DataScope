"use client";

import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";

export function AuthenticatedImage({
  src,
  alt,
  className = "",
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let createdUrl: string | null = null;

    async function load() {
      setIsLoading(true);
      setError(null);
      setObjectUrl(null);

      try {
        const response = await fetch(src, {
          credentials: "include",
          cache: "force-cache",
        });
        if (!response.ok) {
          throw new Error(`Unable to load plot (${response.status})`);
        }
        const blob = await response.blob();
        if (cancelled) {
          return;
        }
        createdUrl = URL.createObjectURL(blob);
        setObjectUrl(createdUrl);
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load plot image.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [src]);

  if (isLoading) {
    return (
      <div className="flex h-full min-h-32 w-full items-center justify-center">
        <Spinner label="Loading plot..." />
      </div>
    );
  }

  if (error || !objectUrl) {
    return (
      <div className="flex h-full min-h-32 w-full flex-col items-center justify-center gap-1 px-3 text-center text-xs text-slate-500">
        <span>Plot unavailable</span>
        {error ? <span className="text-red-600">{error}</span> : null}
      </div>
    );
  }

  return <img alt={alt} className={className} src={objectUrl} />;
}
