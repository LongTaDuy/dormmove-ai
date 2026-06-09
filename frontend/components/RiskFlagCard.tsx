export function RiskFlagCard({ flags }: { flags: string[] }) {
  if (!flags.length) {
    return (
      <div className="rounded-xl border border-success-border bg-success-light p-4">
        <p className="text-sm font-medium text-sage">No risk flags detected.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-warning-border bg-warning-light p-4">
      <h3 className="text-sm font-semibold text-warning">
        Risk flags ({flags.length})
      </h3>
      <ul className="mt-3 space-y-2">
        {flags.map((flag) => (
          <li
            key={flag}
            className="rounded-lg border border-warning-border/60 bg-ivory px-3 py-2 text-sm text-espresso"
          >
            {flag.replace(/_/g, " ")}
          </li>
        ))}
      </ul>
    </div>
  );
}
