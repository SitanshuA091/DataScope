export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_BASE_URL ??
  API_BASE_URL.replace(/^http/, "ws").replace(/\/api\/v1\/?$/, "");

export const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";
