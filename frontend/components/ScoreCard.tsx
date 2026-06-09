import { scorePercent } from "@/lib/format";

export function ScoreCard({
  label,
  score,
  description,
  large,
}: {
  label: string;
  score: number;
  description?: string;
  large?: boolean;
}) {
  const pct = Math.round(score * 100);
  return (
    <div className="rounded-xl border border-border bg-cream/50 p-4">
      <p className="section-title">{label}</p>
      <p
        className={`mt-1 font-bold text-espresso ${large ? "text-3xl" : "text-xl"}`}
      >
        {scorePercent(score)}
      </p>
      {description && (
        <p className="mt-1 text-xs leading-relaxed text-muted">{description}</p>
      )}
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-border/60">
        <div
          className="h-full rounded-full bg-brand transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
