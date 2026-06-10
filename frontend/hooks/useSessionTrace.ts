"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiErrorMessage, getSession, isNetworkError } from "@/lib/api";
import { traceFromSnapshot } from "@/lib/chat";
import type { TraceEntry } from "@/types";

export function useSessionTrace(sessionId: string | undefined) {
  const [trace, setTrace] = useState<TraceEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setErrorMessage(null);
    setIsOffline(false);
    try {
      const snapshot = await getSession(sessionId);
      setTrace(traceFromSnapshot(snapshot.messages));
    } catch (e) {
      setTrace([]);
      setErrorMessage(getApiErrorMessage(e));
      setIsOffline(isNetworkError(e));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    load();
  }, [load]);

  return { trace, loading, errorMessage, isOffline, retry: load };
}
