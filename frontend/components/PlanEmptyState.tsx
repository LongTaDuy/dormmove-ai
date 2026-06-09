import Link from "next/link";

export function PlanEmptyState({
  kind,
}: {
  kind: "no-plan" | "no-session";
}) {
  if (kind === "no-session") {
    return (
      <div className="card p-8 text-center">
        <h3 className="text-lg font-semibold text-espresso">Session not found</h3>
        <p className="mt-2 text-sm text-muted">
          This plan link may be outdated or the session was removed. Start a new
          plan to continue.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link href="/planner" className="btn-primary" aria-label="Start a new plan">
            Start new plan
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-8 text-center">
      <h3 className="text-lg font-semibold text-espresso">No plan yet</h3>
      <p className="mt-2 text-sm text-muted">
        Chat with the planner to generate your checklist, budget, products, and
        timeline. Try the demo prompt for a quick example.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Link href="/planner" className="btn-primary" aria-label="Open planner">
          Go to planner
        </Link>
        <Link
          href="/planner?runDemo=1"
          className="btn-secondary"
          aria-label="Open planner with demo prompt"
        >
          Use demo prompt
        </Link>
      </div>
    </div>
  );
}
