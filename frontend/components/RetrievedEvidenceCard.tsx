import { EvidencePanel } from "@/components/EvidencePanel";
import type { EvidenceItem } from "@/types";

export function RetrievedEvidenceCard({
  evidence,
  helperText,
  compact = true,
  title = "Retrieved evidence",
}: {
  evidence: EvidenceItem[];
  helperText?: string;
  compact?: boolean;
  title?: string;
}) {
  if (!evidence.length) return null;

  return (
    <div className="card border-sage/30 bg-sage/5 p-5">
      <h3 className="section-title text-sage">{title}</h3>
      {helperText ? (
        <p className="mt-2 text-xs leading-relaxed text-muted">{helperText}</p>
      ) : null}
      <div className="mt-4">
        <EvidencePanel evidence={evidence} title="" compact={compact} />
      </div>
    </div>
  );
}
