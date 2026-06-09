"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ChatPanel } from "@/components/ChatPanel";
import { ConnectionError } from "@/components/ConnectionError";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { NextStepsCard } from "@/components/NextStepsCard";
import { ProfileSummary } from "@/components/ProfileSummary";
import { RiskFlagCard } from "@/components/RiskFlagCard";
import { ScoreCard } from "@/components/ScoreCard";
import { SessionListPanel } from "@/components/SessionListPanel";
import { TracePanel } from "@/components/TracePanel";
import {
  createSession,
  getApiErrorMessage,
  getSession,
  isNetworkError,
  isSessionNotFound,
  sendChat,
} from "@/lib/api";
import {
  messagesFromSnapshot,
  missingFieldsFromSnapshot,
  riskFlagsFromSnapshot,
  traceFromSnapshot,
} from "@/lib/chat";
import { DEMO_PROMPT } from "@/lib/constants";
import { missingRequiredFields } from "@/lib/profile";
import {
  clearStoredSessionId,
  getStoredSessionId,
  setStoredSessionId,
} from "@/lib/session";
import { scorePercent, verdictColor } from "@/lib/format";
import type {
  ChatMessage,
  MoveInPlan,
  SessionSnapshotResponse,
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

function hydrateFromSnapshot(snapshot: SessionSnapshotResponse) {
  const plan = snapshot.latest_plan;
  const messages = messagesFromSnapshot(snapshot.messages);
  const missing =
    missingFieldsFromSnapshot(snapshot.messages).length > 0
      ? missingFieldsFromSnapshot(snapshot.messages)
      : missingRequiredFields(snapshot.profile);
  const risk = riskFlagsFromSnapshot(
    snapshot.messages,
    plan?.risk_flags ?? [],
  );
  const trace = traceFromSnapshot(snapshot.messages);

  return {
    profile: snapshot.profile,
    plan,
    messages,
    missingFields: missing,
    riskFlags: risk,
    trace,
  };
}

export function PlannerClient() {
  const searchParams = useSearchParams();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [initLoading, setInitLoading] = useState(true);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [profile, setProfile] = useState<StudentMoveInProfile>(EMPTY_PROFILE);
  const [plan, setPlan] = useState<MoveInPlan | null>(null);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [riskFlags, setRiskFlags] = useState<string[]>([]);
  const [trace, setTrace] = useState<TraceEntry[]>([]);
  const [showTrace, setShowTrace] = useState(false);
  const [demoQueued, setDemoQueued] = useState(false);

  const applySnapshot = useCallback((snapshot: SessionSnapshotResponse) => {
    const state = hydrateFromSnapshot(snapshot);
    setProfile(state.profile);
    setPlan(state.plan);
    setMessages(state.messages);
    setMissingFields(state.missingFields);
    setRiskFlags(state.riskFlags);
    setTrace(state.trace);
    setSessionId(snapshot.session_id);
    setStoredSessionId(snapshot.session_id);
  }, []);

  const resetLocalState = useCallback(() => {
    setMessages([]);
    setProfile(EMPTY_PROFILE);
    setPlan(null);
    setMissingFields([]);
    setRiskFlags([]);
    setTrace([]);
    setShowTrace(false);
  }, []);

  const createAndSelectSession = useCallback(async (title?: string) => {
    const { session_id } = await createSession(title);
    setStoredSessionId(session_id);
    setSessionId(session_id);
    resetLocalState();
    return session_id;
  }, [resetLocalState]);

  const bootstrap = useCallback(async () => {
    setInitLoading(true);
    setConnectionError(null);
    setError(null);
    try {
      const stored = getStoredSessionId();
      if (stored) {
        try {
          const snapshot = await getSession(stored);
          applySnapshot(snapshot);
          return;
        } catch (e) {
          if (isSessionNotFound(e)) {
            clearStoredSessionId();
          } else if (isNetworkError(e)) {
            setConnectionError(getApiErrorMessage(e));
            return;
          } else {
            throw e;
          }
        }
      }
      await createAndSelectSession();
    } catch (e) {
      if (isNetworkError(e)) {
        setConnectionError(getApiErrorMessage(e));
      } else {
        setError(getApiErrorMessage(e));
      }
    } finally {
      setInitLoading(false);
    }
  }, [applySnapshot, createAndSelectSession]);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const handleSend = useCallback(
    async (message: string) => {
      if (!sessionId) return;
      setChatLoading(true);
      setError(null);
      setMessages((prev) => [...prev, { role: "user", content: message }]);
      try {
        await sendChat(sessionId, message);
        const snapshot = await getSession(sessionId);
        applySnapshot(snapshot);
      } catch (e) {
        setMessages((prev) => prev.slice(0, -1));
        setError(getApiErrorMessage(e));
      } finally {
        setChatLoading(false);
      }
    },
    [sessionId, applySnapshot],
  );

  useEffect(() => {
    if (searchParams.get("runDemo") === "1") {
      setDemoQueued(true);
    }
  }, [searchParams]);

  useEffect(() => {
    if (demoQueued && sessionId && !initLoading && !chatLoading) {
      setDemoQueued(false);
      handleSend(DEMO_PROMPT);
    }
  }, [demoQueued, sessionId, initLoading, chatLoading, handleSend]);

  async function loadSession(id: string) {
    setInitLoading(true);
    setError(null);
    try {
      const snapshot = await getSession(id);
      applySnapshot(snapshot);
    } catch (e) {
      setError(getApiErrorMessage(e));
    } finally {
      setInitLoading(false);
    }
  }

  async function handleNewPlan() {
    clearStoredSessionId();
    setError(null);
    try {
      await createAndSelectSession("New DormMove Plan");
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  }

  if (initLoading && !connectionError) {
    return (
      <AppShell>
        <LoadingState message="Recovering your plan…" />
      </AppShell>
    );
  }

  if (connectionError) {
    return (
      <AppShell>
        <ConnectionError message={connectionError} onRetry={bootstrap} />
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
              Session {sessionId.slice(0, 8)}… · restored from local storage
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleNewPlan}
            className="btn-ghost"
            aria-label="Start a new plan"
          >
            Start new plan
          </button>
          <button
            type="button"
            onClick={() => handleSend(DEMO_PROMPT)}
            disabled={chatLoading || !sessionId}
            className="btn-accent"
            aria-label="Run demo move-in prompt"
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
          <SessionListPanel
            currentSessionId={sessionId}
            onSelectSession={loadSession}
            onNewPlan={handleNewPlan}
          />

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

          {plan && sessionId && <NextStepsCard sessionId={sessionId} />}

          {plan && sessionId && (
            <div className="card p-5">
              <h3 className="section-title">Explore your plan</h3>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <PlanLink href={`/results/${sessionId}`} label="Results" primary />
                <PlanLink href={`/checklist/${sessionId}`} label="Checklist" />
                <PlanLink href={`/products/${sessionId}`} label="Products" />
                <PlanLink href={`/timeline/${sessionId}`} label="Timeline" />
              </div>
            </div>
          )}

          <div className="card p-4">
            <button
              type="button"
              onClick={() => setShowTrace((v) => !v)}
              className="text-sm font-medium text-muted hover:text-espresso focus:outline-none focus:underline"
              aria-expanded={showTrace}
              aria-label="Toggle agent trace debug panel"
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
