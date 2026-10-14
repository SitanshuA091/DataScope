export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatBytes(bytes: number) {
  if (bytes === 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );

  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatNumber(
  value: number | null | undefined,
  decimals = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  return Number.isInteger(value)
    ? value.toLocaleString()
    : value.toLocaleString(undefined, { maximumFractionDigits: decimals });
}

export function formatPercent(
  value: number | null | undefined,
  decimals = 1,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  return `${value.toFixed(decimals)}%`;
}

export function formatDuration(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || Number.isNaN(ms)) {
    return "N/A";
  }
  if (ms < 1000) {
    return `${Math.round(ms)} ms`;
  }
  return `${(ms / 1000).toFixed(2)} s`;
}
