"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getApiErrorMessage,
  isNetworkError,
  isNoPlanError,
  isSessionNotFound,
} from "@/lib/api";

export type PlanResourceStatus =
  | "loading"
  | "ready"
  | "no-session"
  | "no-plan"
  | "error";

export function usePlanResource<T>(
  sessionId: string | undefined,
  fetcher: (id: string) => Promise<T>,
) {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<PlanResourceStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastError, setLastError] = useState<unknown>(null);

  const load = useCallback(async () => {
    if (!sessionId) return;
    setStatus("loading");
    setErrorMessage(null);
    setLastError(null);
    try {
      const result = await fetcher(sessionId);
      setData(result);
      setStatus("ready");
    } catch (e) {
      setData(null);
      setLastError(e);
      if (isSessionNotFound(e)) {
        setStatus("no-session");
      } else if (isNoPlanError(e)) {
        setStatus("no-plan");
      } else {
        setStatus("error");
        setErrorMessage(getApiErrorMessage(e));
      }
    }
  }, [sessionId, fetcher]);

  useEffect(() => {
    load();
  }, [load]);

  return {
    data,
    status,
    errorMessage,
    isOffline: status === "error" && isNetworkError(lastError),
    retry: load,
  };
}
