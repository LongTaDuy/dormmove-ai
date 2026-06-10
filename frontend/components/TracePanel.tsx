"use client";

import { useMemo, useState } from "react";
import type { TraceEntry } from "@/types";
import { riskLevelColor, sourceTypeLabel } from "@/lib/format";

export function TracePanel({ trace }: { trace: TraceEntry[] }) {
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [expandedEvidence, setExpandedEvidence] = useState<Set<string>>(new Set());

  const grouped = useMemo(() => groupTraceByAgent(trace), [trace]);

  if (!trace.length) {
    return (
      <p className="text-sm text-muted">No agent trace yet. Send a message.</p>
    );
  }

  function toggleAgent(agent: string) {
    setExpandedAgents((prev) => {
      const next = new Set(prev);
      if (next.has(agent)) next.delete(agent);
      else next.add(agent);
      return next;
    });
  }

  function toggleEvidence(key: string) {
    setExpandedEvidence((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <div className="max-h-96 space-y-3 overflow-y-auto">
      {grouped.map(({ agent, entries }) => {
        const agentOpen = expandedAgents.has(agent);
        const evidenceTotal = entries.reduce(
          (n, e) => n + (e.evidence?.length ?? 0),
          0,
        );

        return (
          <div
            key={agent}
            className="rounded-xl border border-border bg-cream/40"
          >
            <button
              type="button"
              onClick={() => toggleAgent(agent)}
              className="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left focus:outline-none focus:ring-2 focus:ring-brand/20"
              aria-expanded={agentOpen}
            >
              <span className="text-sm font-semibold text-brand">{agent}</span>
              <span className="text-xs text-muted">
                {entries.length} step{entries.length === 1 ? "" : "s"}
                {evidenceTotal > 0 ? ` · ${evidenceTotal} evidence` : ""}
                {agentOpen ? " ▾" : " ▸"}
              </span>
            </button>

            {agentOpen && (
              <div className="space-y-2 border-t border-border px-3 py-2">
                {entries.map((entry, i) => {
                  const evidenceKey = `${agent}-${entry.action}-${i}`;
                  const hasEvidence = Boolean(entry.evidence?.length);
                  const evidenceOpen = expandedEvidence.has(evidenceKey);

                  return (
                    <div
                      key={evidenceKey}
                      className="rounded-lg border border-border/80 bg-ivory p-3 text-xs"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="font-medium text-espresso">{entry.action}</p>
                        {hasEvidence ? (
                          <span className="badge border border-sage/30 bg-sage/10 text-sage">
                            {entry.evidence!.length} evidence
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-1 leading-relaxed text-muted">
                        {entry.summary}
                      </p>

                      {hasEvidence && (
                        <div className="mt-2">
                          <button
                            type="button"
                            onClick={() => toggleEvidence(evidenceKey)}
                            className="text-xs font-medium text-brand hover:underline focus:outline-none"
                            aria-expanded={evidenceOpen}
                          >
                            {evidenceOpen
                              ? "▾ Hide evidence used"
                              : "▸ Evidence used"}
                          </button>
                          {evidenceOpen && (
                            <ul className="mt-2 space-y-2">
                              {entry.evidence!.map((item) => (
                                <li
                                  key={item.doc_id}
                                  className="rounded-lg border border-border bg-cream/50 p-2"
                                >
                                  <div className="flex flex-wrap items-start justify-between gap-2">
                                    <div>
                                      <p className="font-medium text-espresso">
                                        {item.title}
                                      </p>
                                      <p className="font-mono text-[10px] text-muted">
                                        {item.doc_id}
                                      </p>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.risk_level ? (
                                        <span
                                          className={`badge border px-1.5 py-0 text-[10px] ${riskLevelColor(item.risk_level)}`}
                                        >
                                          {item.risk_level}
                                        </span>
                                      ) : null}
                                      {item.source_type ? (
                                        <span className="badge border border-border bg-ivory px-1.5 py-0 text-[10px] text-muted">
                                          {sourceTypeLabel(item.source_type)}
                                        </span>
                                      ) : null}
                                      {item.score != null ? (
                                        <span className="badge border border-brand/20 bg-brand-light px-1.5 py-0 text-[10px] text-brand">
                                          {item.score.toFixed(2)}
                                        </span>
                                      ) : null}
                                    </div>
                                  </div>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function groupTraceByAgent(trace: TraceEntry[]) {
  const map = new Map<string, TraceEntry[]>();
  for (const entry of trace) {
    const list = map.get(entry.agent) ?? [];
    list.push(entry);
    map.set(entry.agent, list);
  }
  return Array.from(map.entries()).map(([agent, entries]) => ({
    agent,
    entries,
  }));
}
