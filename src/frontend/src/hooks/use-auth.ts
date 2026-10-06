"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, apiFetch } from "@/lib/api-client";
import { API_BASE_URL, USE_MOCKS } from "@/lib/constants";
import { mockUser } from "@/lib/mock-data";
import type { CurrentUser } from "@/types/auth";

export function useAuth() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (USE_MOCKS) {
      setUser(mockUser);
      setError(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const currentUser = await apiFetch<CurrentUser>("/auth/me");
      setUser(currentUser);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 401) {
        setUser(null);
      } else {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load the current user.",
        );
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(refresh);
  }, [refresh]);

  const loginWithGoogle = useCallback(() => {
    window.open(`${API_BASE_URL}/auth/google/login`, "_self");
  }, []);

  const logout = useCallback(async () => {
    if (USE_MOCKS) {
      setUser(null);
      return;
    }

    await apiFetch<void>("/auth/logout", { method: "POST" });
    setUser(null);
  }, []);

  return { user, isLoading, error, refresh, loginWithGoogle, logout };
}
