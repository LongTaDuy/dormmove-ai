"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ChecklistTable } from "@/components/ChecklistTable";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { ApiError, getChecklist } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { ChecklistEnvelopeResponse } from "@/types";

export default function ChecklistPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [data, setData] = useState<ChecklistEnvelopeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    getChecklist(sessionId)
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
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <h1 className="page-title">Dorm checklist</h1>
        {s && (
          <div className="rounded-xl border border-brand/30 bg-brand-light px-4 py-2">
            <p className="text-xs font-medium text-brand">Est. remaining cost</p>
            <p className="text-xl font-bold text-brand-dark">
              {formatCurrency(s.estimated_remaining_cost)}
            </p>
          </div>
        )}
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} />}
      {notFound && (
        <EmptyState
          title="No checklist yet"
          message="Generate a plan in the planner first."
        />
      )}

      {data && s && (
        <div className="space-y-6">
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
