"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { TimelineList } from "@/components/TimelineList";
import { ApiError, getTimeline } from "@/lib/api";
import { categoryLabel } from "@/lib/format";
import type { TimelineEnvelopeResponse } from "@/types";

export default function TimelinePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [data, setData] = useState<TimelineEnvelopeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    getTimeline(sessionId)
      .then(setData)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) setNotFound(true);
        else setError(e instanceof Error ? e.message : "Failed to load");
      })
      .finally(() => setLoading(false));
  }, [sessionId]);

  const s = data?.summary;

  return (
    <AppShell sessionId={sessionId}>
      <h1 className="page-title mb-6">Move-in timeline</h1>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} />}
      {notFound && (
        <EmptyState
          title="No timeline yet"
          message="Generate a plan in the planner first."
        />
      )}

      {data && s && (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-3">
            <StatCard label="Tasks" value={String(s.total_tasks)} />
            <StatCard label="Phases" value={String(s.phases.length)} />
            <StatCard
              label="Risk flags"
              value={String(s.risk_flag_count)}
              warn={s.risk_flag_count > 0}
            />
          </div>

          {s.phases.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {s.phases.map((phase) => (
                <span
                  key={phase}
                  className="badge border border-sage/30 bg-sage/10 text-sage"
                >
                  {categoryLabel(phase)}
                </span>
              ))}
            </div>
          )}

          <TimelineList tasks={data.timeline} />
        </div>
      )}
    </AppShell>
  );
}

function StatCard({
  label,
  value,
  warn,
}: {
  label: string;
  value: string;
  warn?: boolean;
}) {
  return (
    <div
      className={`stat-card ${warn ? "border-warning-border bg-warning-light" : ""}`}
    >
      <p className="text-xs font-medium text-muted">{label}</p>
      <p
        className={`mt-1 text-xl font-bold ${warn ? "text-warning" : "text-espresso"}`}
      >
        {value}
      </p>
    </div>
  );
}
