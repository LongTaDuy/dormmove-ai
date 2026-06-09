"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ConnectionError } from "@/components/ConnectionError";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PlanEmptyState } from "@/components/PlanEmptyState";
import { RiskFlagCard } from "@/components/RiskFlagCard";
import { ScoreCard } from "@/components/ScoreCard";
import { getPlan } from "@/lib/api";
import { usePlanResource } from "@/hooks/usePlanResource";
import { scorePercent, verdictColor } from "@/lib/format";

const SCORE_HELPERS: Record<string, string> = {
  Readiness: "Profile completeness and essential item coverage.",
  "Budget fit": "How well estimated costs fit your budget.",
  "Dorm compliance": "Generic dorm-rule safety for flagged items.",
  Logistics: "Shipping timing and transportation feasibility.",
  "Product trust": "Review depth and fit of recommended products.",
};

export default function ResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data: plan, status, errorMessage, isOffline, retry } =
    usePlanResource(sessionId, getPlan);

  const scores = plan
    ? [
        { label: "Readiness", value: plan.score_breakdown.readiness_score },
        { label: "Budget fit", value: plan.score_breakdown.budget_fit_score },
        {
          label: "Dorm compliance",
          value: plan.score_breakdown.dorm_compliance_score,
        },
        { label: "Logistics", value: plan.score_breakdown.logistics_score },
        {
          label: "Product trust",
          value: plan.score_breakdown.product_trust_score,
        },
      ]
    : [];

  return (
    <AppShell sessionId={sessionId}>
      <h1 className="page-title mb-6">Move-in results</h1>

      {status === "loading" && <LoadingState message="Loading plan…" />}
      {status === "no-session" && <PlanEmptyState kind="no-session" />}
      {status === "no-plan" && <PlanEmptyState kind="no-plan" />}
      {status === "error" && isOffline && (
        <ConnectionError message={errorMessage ?? ""} onRetry={retry} />
      )}
      {status === "error" && !isOffline && (
        <ErrorState message={errorMessage ?? ""} onRetry={retry} />
      )}

      {status === "ready" && plan && (
        <div className="space-y-6">
          <div className="card border-brand/25 bg-gradient-to-br from-brand-light to-ivory p-8 text-center">
            <p className="section-title">Final move-in score</p>
            <p className="mt-2 text-6xl font-bold text-brand">
              {scorePercent(plan.score_breakdown.final_move_in_score)}
            </p>
            <span
              className={`badge mt-4 border px-4 py-1.5 text-sm ${verdictColor(plan.score_breakdown.verdict)}`}
            >
              {plan.score_breakdown.verdict.replace(/_/g, " ")}
            </span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {scores.map(({ label, value }) => (
              <ScoreCard
                key={label}
                label={label}
                score={value}
                description={SCORE_HELPERS[label]}
              />
            ))}
          </div>

          {plan.score_breakdown.top_reasons.length > 0 && (
            <div className="card p-6">
              <h3 className="section-title">Top reasons</h3>
              <ul className="mt-4 space-y-2">
                {plan.score_breakdown.top_reasons.map((r) => (
                  <li
                    key={r}
                    className="flex gap-3 rounded-lg bg-cream/50 px-4 py-3 text-sm text-espresso"
                  >
                    <span className="text-brand">•</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <RiskFlagCard flags={plan.score_breakdown.risk_flags} />

          {plan.final_summary && (
            <div className="card p-6">
              <h3 className="section-title">Summary</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted">
                {plan.final_summary}
              </p>
            </div>
          )}

          <div className="card p-5">
            <h3 className="section-title">Quick links</h3>
            <div className="mt-4 flex flex-wrap gap-2">
              <NavLink href={`/checklist/${sessionId}`} label="Checklist" />
              <NavLink href={`/products/${sessionId}`} label="Products" />
              <NavLink href={`/timeline/${sessionId}`} label="Timeline" />
              <NavLink href="/planner" label="Back to planner" />
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="btn-secondary py-2">
      {label}
    </Link>
  );
}
