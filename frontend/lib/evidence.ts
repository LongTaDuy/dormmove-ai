import type { EvidenceItem, TraceEntry } from "@/types";

const RETRIEVAL_ACTIONS = new Set([
  "retrieved_rule_context",
  "retrieved_checklist_context",
  "retrieved_budget_context",
  "retrieved_timeline_context",
]);

/** De-duplicate evidence items by doc_id, preserving first occurrence order. */
export function dedupeEvidence(items: EvidenceItem[]): EvidenceItem[] {
  const seen = new Set<string>();
  const result: EvidenceItem[] = [];
  for (const item of items) {
    if (!seen.has(item.doc_id)) {
      seen.add(item.doc_id);
      result.push(item);
    }
  }
  return result;
}

/** Collect all evidence from trace entries, optionally filtered by action names. */
export function evidenceFromTrace(
  trace: TraceEntry[],
  actions?: string[],
): EvidenceItem[] {
  const actionSet = actions ? new Set(actions) : null;
  const collected: EvidenceItem[] = [];

  for (const entry of trace) {
    if (actionSet && !actionSet.has(entry.action)) continue;
    if (entry.evidence?.length) {
      collected.push(...entry.evidence);
    }
  }

  return dedupeEvidence(collected);
}

/** Top N unique evidence items from trace (retrieval actions only by default). */
export function topEvidenceFromTrace(
  trace: TraceEntry[],
  limit = 5,
  actions: string[] = Array.from(RETRIEVAL_ACTIONS),
): EvidenceItem[] {
  return evidenceFromTrace(trace, actions).slice(0, limit);
}

export const EVIDENCE_ACTIONS = {
  rules: ["retrieved_rule_context", "audited_rules"],
  checklist: ["retrieved_checklist_context", "retrieved_rule_context"],
  timeline: ["retrieved_timeline_context"],
  budget: ["retrieved_budget_context"],
  all: Array.from(RETRIEVAL_ACTIONS),
} as const;
