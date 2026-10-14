import { API_BASE_URL } from "./constants";
import type { ArtifactItem } from "@/types/analysis";

export function resolveArtifactUrl(artifact: ArtifactItem): string | null {
  if (artifact.url) {
    if (artifact.url.startsWith("http")) {
      return artifact.url;
    }
    if (artifact.url.startsWith("/api/")) {
      const backendOrigin = API_BASE_URL.replace(/\/api\/v1\/?$/, "");
      return `${backendOrigin}${artifact.url}`;
    }
    if (artifact.url.startsWith("/")) {
      return `${API_BASE_URL.replace(/\/api\/v1\/?$/, "")}${artifact.url}`;
    }
    return `${API_BASE_URL}/${artifact.url.replace(/^\//, "")}`;
  }

  const artifactId =
    artifact.id || (artifact.metadata?.id as string | undefined);
  if (artifactId) {
    return `${API_BASE_URL}/artifacts/${artifactId}/content`;
  }

  return null;
}

export function artifactCaption(artifact: ArtifactItem): string {
  return (
    artifact.title ||
    (artifact.metadata?.title as string | undefined) ||
    artifact.artifact_type.replaceAll("_", " ")
  );
}

export function artifactKind(artifact: ArtifactItem): string {
  return (
    artifact.kind ||
    (artifact.metadata?.kind as string | undefined) ||
    artifact.artifact_type
  );
}

export function artifactColumns(artifact: ArtifactItem): string[] {
  if (Array.isArray(artifact.columns)) {
    return artifact.columns.map(String);
  }
  const fromMeta = artifact.metadata?.columns;
  if (Array.isArray(fromMeta)) {
    return fromMeta.map(String);
  }
  return [];
}
