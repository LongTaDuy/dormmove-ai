"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ConnectionError } from "@/components/ConnectionError";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PlanEmptyState } from "@/components/PlanEmptyState";
import { TimelineList } from "@/components/TimelineList";
import { RetrievedEvidenceCard } from "@/components/RetrievedEvidenceCard";
import { getTimeline } from "@/lib/api";
import { EVIDENCE_ACTIONS, evidenceFromTrace } from "@/lib/evidence";
import { usePlanResource } from "@/hooks/usePlanResource";
import { useSessionTrace } from "@/hooks/useSessionTrace";
import { categoryLabel } from "@/lib/format";

export default function TimelinePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, status, errorMessage, isOffline, retry } = usePlanResource(
    sessionId,
    getTimeline,
  );
  const { trace } = useSessionTrace(sessionId);
  const timelineEvidence = evidenceFromTrace(trace, [
    ...EVIDENCE_ACTIONS.timeline,
  ]);

  const s = data?.summary;

  return (
    <AppShell sessionId={sessionId}>
      <h1 className="page-title mb-6">Move-in timeline</h1>

      {status === "loading" && <LoadingState />}
      {status === "no-session" && <PlanEmptyState kind="no-session" />}
      {status === "no-plan" && <PlanEmptyState kind="no-plan" />}
      {status === "error" && isOffline && (
        <ConnectionError message={errorMessage ?? ""} onRetry={retry} />
      )}
      {status === "error" && !isOffline && (
        <ErrorState message={errorMessage ?? ""} onRetry={retry} />
      )}

      {status === "ready" && data && s && (
        <div className="space-y-6">
          <RetrievedEvidenceCard
            evidence={timelineEvidence.slice(0, 4)}
            title="Logistics evidence"
            helperText="Local knowledge snippets supporting timeline and shipping guidance."
            compact
          />

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
