import type { TraceEntry } from "@/types";

export function TracePanel({ trace }: { trace: TraceEntry[] }) {
  if (!trace.length) {
    return (
      <p className="text-sm text-muted">No agent trace yet. Send a message.</p>
    );
  }

  return (
    <div className="max-h-64 space-y-2 overflow-y-auto">
      {trace.map((entry, i) => (
        <div
          key={i}
          className="rounded-lg border border-border bg-cream/50 p-3 text-xs"
        >
          <p className="font-semibold text-brand">{entry.agent}</p>
          <p className="text-muted">{entry.action}</p>
          <p className="mt-1 leading-relaxed text-espresso/80">{entry.summary}</p>
        </div>
      ))}
    </div>
  );
}
