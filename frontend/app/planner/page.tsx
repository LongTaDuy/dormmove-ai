"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { ChatPanel } from "@/components/ChatPanel";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { ProfileSummary } from "@/components/ProfileSummary";
import { RiskFlagCard } from "@/components/RiskFlagCard";
import { ScoreCard } from "@/components/ScoreCard";
import { TracePanel } from "@/components/TracePanel";
import { ApiError, createSession, sendChat } from "@/lib/api";
import { DEMO_PROMPT } from "@/lib/constants";
import {
  clearStoredSessionId,
  getStoredSessionId,
  setStoredSessionId,
} from "@/lib/session";
import { scorePercent, verdictColor } from "@/lib/format";
import type {
  ChatMessage,
  MoveInPlan,
  StudentMoveInProfile,
  TraceEntry,
} from "@/types";

const EMPTY_PROFILE: StudentMoveInProfile = {
  school_name: null,
  dorm_name: null,
  room_type: "unknown",
  move_in_date: null,
  budget_total: null,
  budget_preference: "balanced",
  already_owned_items: [],
  roommate_items: [],
  dietary_or_health_needs: [],
  climate_or_location_notes: null,
  transportation_mode: "unknown",
  restrictions: [],
  preferences: [],
};

export default function PlannerPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [initLoading, setInitLoading] = useState(true);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [profile, setProfile] = useState<StudentMoveInProfile>(EMPTY_PROFILE);
  const [plan, setPlan] = useState<MoveInPlan | null>(null);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [riskFlags, setRiskFlags] = useState<string[]>([]);
  const [trace, setTrace] = useState<TraceEntry[]>([]);
  const [showTrace, setShowTrace] = useState(false);

  const initSession = useCallback(async () => {
    setInitLoading(true);
    setError(null);
    try {
      const stored = getStoredSessionId();
      if (stored) {
        setSessionId(stored);
      } else {
        const { session_id } = await createSession();
        setStoredSessionId(session_id);
        setSessionId(session_id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create session");
    } finally {
      setInitLoading(false);
    }
  }, []);

  useEffect(() => {
    initSession();
  }, [initSession]);

  async function handleNewPlan() {
    clearStoredSessionId();
    setMessages([]);
    setProfile(EMPTY_PROFILE);
    setPlan(null);
    setMissingFields([]);
    setRiskFlags([]);
    setTrace([]);
    setShowTrace(false);
    try {
      const { session_id } = await createSession("New DormMove Plan");
      setStoredSessionId(session_id);
      setSessionId(session_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create session");
    }
  }

  async function handleSend(message: string) {
    if (!sessionId) return;
    setChatLoading(true);
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    try {
      const res = await sendChat(sessionId, message);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.reply },
      ]);
      setProfile(res.profile);
      setMissingFields(res.missing_fields);
      setRiskFlags(res.risk_flags);
      setTrace(res.trace);
      if (res.plan) setPlan(res.plan);
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.detail ?? e.message : "Chat failed";
      setError(msg);
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setChatLoading(false);
    }
  }

  if (initLoading) {
    return (
      <AppShell>
        <LoadingState message="Starting planner…" />
      </AppShell>
    );
  }

  const score = plan?.score_breakdown;

  return (
    <AppShell sessionId={sessionId}>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Move-in planner</h1>
          {sessionId && (
            <p className="mt-1 text-sm text-muted">
              Session {sessionId.slice(0, 8)}…
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={handleNewPlan} className="btn-ghost">
            Start new plan
          </button>
          <button
            type="button"
            onClick={() => handleSend(DEMO_PROMPT)}
            disabled={chatLoading || !sessionId}
            className="btn-accent"
          >
            Run demo
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6">
          <ErrorState message={error} onRetry={() => setError(null)} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <ChatPanel
            messages={messages}
            onSend={handleSend}
            loading={chatLoading}
            disabled={!sessionId}
          />
        </div>

        <div className="space-y-5 lg:col-span-2">
          <ProfileSummary profile={profile} missingFields={missingFields} />

          {score && (
            <div className="card border-brand/20 p-5">
              <div className="flex items-center justify-between gap-2">
                <h3 className="section-title">Move-in score</h3>
                <span
                  className={`badge border ${verdictColor(score.verdict)}`}
                >
                  {score.verdict.replace(/_/g, " ")}
                </span>
              </div>
              <p className="mt-2 text-4xl font-bold text-brand">
                {scorePercent(score.final_move_in_score)}
              </p>
              <div className="mt-4 grid grid-cols-2 gap-2">
                <ScoreCard label="Readiness" score={score.readiness_score} />
                <ScoreCard label="Budget" score={score.budget_fit_score} />
                <ScoreCard label="Compliance" score={score.dorm_compliance_score} />
                <ScoreCard label="Logistics" score={score.logistics_score} />
              </div>
            </div>
          )}

          <RiskFlagCard flags={riskFlags} />

          {plan && sessionId && (
            <div className="card p-5">
              <h3 className="section-title">Explore your plan</h3>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <PlanLink href={`/results/${sessionId}`} label="Results" primary />
                <PlanLink href={`/checklist/${sessionId}`} label="Checklist" />
                <PlanLink href={`/products/${sessionId}`} label="Products" />
                <PlanLink href={`/timeline/${sessionId}`} label="Timeline" />
              </div>
              {plan.checklist.length > 0 && (
                <p className="mt-4 text-sm text-muted">
                  {plan.checklist.filter((c) => c.status === "needed").length}{" "}
                  items to buy · {plan.product_candidates.length} product picks
                </p>
              )}
            </div>
          )}

          <div className="card p-4">
            <button
              type="button"
              onClick={() => setShowTrace((v) => !v)}
              className="text-sm font-medium text-muted hover:text-espresso focus:outline-none focus:underline"
            >
              {showTrace ? "▾ Hide agent trace" : "▸ Show agent trace (debug)"}
            </button>
            {showTrace && (
              <div className="mt-3 border-t border-border pt-3">
                <TracePanel trace={trace} />
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function PlanLink({
  href,
  label,
  primary,
}: {
  href: string;
  label: string;
  primary?: boolean;
}) {
  return (
    <Link
      href={href}
      className={
        primary
          ? "btn-primary py-2.5 text-center"
          : "rounded-xl border border-border bg-cream/50 px-3 py-2.5 text-center text-sm font-medium text-espresso transition hover:border-brand/40 hover:bg-brand-light hover:text-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
      }
    >
      {label}
    </Link>
  );
}
