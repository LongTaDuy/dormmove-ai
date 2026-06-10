"use client";

import { useState } from "react";
import type { EvidenceItem } from "@/types";
import { dedupeEvidence } from "@/lib/evidence";
import { riskLevelColor, sourceTypeLabel } from "@/lib/format";

export function EvidencePanel({
  evidence,
  title = "Evidence",
  compact = false,
}: {
  evidence: EvidenceItem[];
  title?: string;
  compact?: boolean;
}) {
  const items = dedupeEvidence(evidence);

  if (!items.length) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-cream/40 px-4 py-6 text-center">
        <p className="text-sm text-muted">No retrieved evidence yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {title ? <h4 className="text-sm font-semibold text-espresso">{title}</h4> : null}
      <ul className="space-y-2">
        {items.map((item) => (
          <EvidenceCard key={item.doc_id} item={item} compact={compact} />
        ))}
      </ul>
    </div>
  );
}

function EvidenceCard({
  item,
  compact,
}: {
  item: EvidenceItem;
  compact: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasDetails = Boolean(item.content || item.tags?.length);

  return (
    <li className="rounded-xl border border-border bg-ivory p-3 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-espresso">{item.title}</p>
          <p className="mt-0.5 font-mono text-xs text-muted">{item.doc_id}</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {item.risk_level ? (
            <span
              className={`badge border ${riskLevelColor(item.risk_level)}`}
            >
              {item.risk_level} risk
            </span>
          ) : null}
          {item.source_type ? (
            <span className="badge border border-border bg-cream/60 text-muted">
              {sourceTypeLabel(item.source_type)}
            </span>
          ) : null}
          {item.score != null ? (
            <span className="badge border border-brand/20 bg-brand-light text-brand">
              score {item.score.toFixed(2)}
            </span>
          ) : null}
        </div>
      </div>

      {!compact && hasDetails && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-xs font-medium text-brand hover:underline focus:outline-none focus:ring-2 focus:ring-brand/30"
            aria-expanded={expanded}
            aria-label={expanded ? "Hide evidence details" : "Show evidence details"}
          >
            {expanded ? "Hide details" : "Show details"}
          </button>
          {expanded && (
            <div className="mt-2 space-y-2 border-t border-border pt-2">
              {item.content ? (
                <p className="text-xs leading-relaxed text-muted">{item.content}</p>
              ) : null}
              {item.tags?.length ? (
                <div className="flex flex-wrap gap-1">
                  {item.tags.map((tag) => (
                    <span
                      key={tag}
                      className="badge border border-sage/30 bg-sage/5 text-sage"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          )}
        </div>
      )}
    </li>
  );
}
