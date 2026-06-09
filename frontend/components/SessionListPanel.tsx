"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiErrorMessage, listSessions } from "@/lib/api";
import { formatDate, scorePercent, verdictColor } from "@/lib/format";
import type { SessionSummary } from "@/types";

export function SessionListPanel({
  currentSessionId,
  onSelectSession,
  onNewPlan,
}: {
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewPlan: () => void;
}) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await listSessions();
      setSessions(list.slice(0, 5));
    } catch (e) {
      setError(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, currentSessionId]);

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="section-title">Recent plans</h3>
        <button
          type="button"
          onClick={onNewPlan}
          className="text-xs font-semibold text-brand hover:underline focus:outline-none focus:ring-2 focus:ring-brand/30"
          aria-label="Create a new plan"
        >
          + New plan
        </button>
      </div>

      {loading && (
        <p className="mt-3 text-sm text-muted">Loading sessions…</p>
      )}
      {error && (
        <p className="mt-3 text-xs text-warning">{error}</p>
      )}

      {!loading && !error && sessions.length === 0 && (
        <p className="mt-3 text-sm text-muted">No saved plans yet.</p>
      )}

      <ul className="mt-3 space-y-2">
        {sessions.map((s) => {
          const active = s.session_id === currentSessionId;
          return (
            <li key={s.session_id}>
              <button
                type="button"
                onClick={() => onSelectSession(s.session_id)}
                className={`w-full rounded-xl border px-3 py-2.5 text-left transition focus:outline-none focus:ring-2 focus:ring-brand/30 ${
                  active
                    ? "border-brand/40 bg-brand-light"
                    : "border-border bg-cream/40 hover:border-border-dark hover:bg-cream"
                }`}
                aria-label={`Load plan ${s.title}`}
                aria-current={active ? "true" : undefined}
              >
                <p className="truncate text-sm font-medium text-espresso">
                  {s.title}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
                  {s.latest_score != null && (
                    <span className="font-medium text-brand">
                      {scorePercent(s.latest_score)}
                    </span>
                  )}
                  {s.latest_verdict && (
                    <span
                      className={`badge border px-1.5 py-0 ${verdictColor(s.latest_verdict)}`}
                    >
                      {s.latest_verdict.replace(/_/g, " ")}
                    </span>
                  )}
                  {s.updated_at && (
                    <span>{formatDate(s.updated_at)}</span>
                  )}
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
