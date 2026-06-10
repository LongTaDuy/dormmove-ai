"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ChecklistTable } from "@/components/ChecklistTable";
import { ConnectionError } from "@/components/ConnectionError";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PlanEmptyState } from "@/components/PlanEmptyState";
import { RetrievedEvidenceCard } from "@/components/RetrievedEvidenceCard";
import { getChecklist } from "@/lib/api";
import { EVIDENCE_ACTIONS, evidenceFromTrace } from "@/lib/evidence";
import { usePlanResource } from "@/hooks/usePlanResource";
import { useSessionTrace } from "@/hooks/useSessionTrace";
import { formatCurrency } from "@/lib/format";

export default function ChecklistPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, status, errorMessage, isOffline, retry } = usePlanResource(
    sessionId,
    getChecklist,
  );
  const { trace } = useSessionTrace(sessionId);
  const checklistEvidence = evidenceFromTrace(trace, [
    ...EVIDENCE_ACTIONS.checklist,
  ]);

  const s = data?.summary;

  return (
    <AppShell sessionId={sessionId}>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <h1 className="page-title">Dorm checklist</h1>
        {s && status === "ready" && (
          <div className="rounded-xl border border-brand/30 bg-brand-light px-4 py-2">
            <p className="text-xs font-medium text-brand">Est. remaining cost</p>
            <p className="text-xl font-bold text-brand-dark">
              {formatCurrency(s.estimated_remaining_cost)}
            </p>
          </div>
        )}
      </div>

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
            evidence={checklistEvidence.slice(0, 4)}
            title="Packing & rule evidence"
            helperText="Grounding snippets for checklist and generic dorm-rule items."
            compact
          />

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <StatCard label="Total" value={String(s.total)} />
            <StatCard label="Needed" value={String(s.needed)} highlight />
            <StatCard label="Owned" value={String(s.already_owned)} />
            <StatCard label="Roommate" value={String(s.roommate_has)} />
            <StatCard label="Check rules" value={String(s.check_rules)} />
            <StatCard
              label="Est. cost"
              value={formatCurrency(s.estimated_remaining_cost)}
            />
          </div>
          <ChecklistTable items={data.checklist} />
        </div>
      )}
    </AppShell>
  );
}

function StatCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`stat-card ${highlight ? "border-brand/30 bg-brand-light" : ""}`}
    >
      <p className="text-xs font-medium text-muted">{label}</p>
      <p className="mt-1 text-xl font-bold text-espresso">{value}</p>
    </div>
  );
}
