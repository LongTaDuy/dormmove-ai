import Link from "next/link";

const STEPS = [
  {
    label: "Review score breakdown",
    href: (id: string) => `/results/${id}`,
    desc: "See your move-in readiness verdict and component scores.",
  },
  {
    label: "Check rule-risk items",
    href: (id: string) => `/checklist/${id}`,
    desc: "Filter checklist items that need dorm-rule confirmation.",
  },
  {
    label: "Review product shortlist",
    href: (id: string) => `/products/${id}`,
    desc: "Browse category-level picks within your budget.",
  },
  {
    label: "Review move-in timeline",
    href: (id: string) => `/timeline/${id}`,
    desc: "See phased tasks and shipping deadlines.",
  },
] as const;

export function NextStepsCard({ sessionId }: { sessionId: string }) {
  return (
    <div className="card border-sage/30 bg-sage/5 p-5">
      <h3 className="text-sm font-semibold text-sage">Next steps</h3>
      <p className="mt-1 text-xs text-muted">
        Your plan is ready — review these areas before move-in day.
      </p>
      <ol className="mt-4 space-y-3">
        {STEPS.map((step, i) => (
          <li key={step.label}>
            <Link
              href={step.href(sessionId)}
              className="group block rounded-xl border border-border bg-ivory px-4 py-3 transition hover:border-sage/40 hover:shadow-soft focus:outline-none focus:ring-2 focus:ring-sage/30"
              aria-label={step.label}
            >
              <span className="flex items-start gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sage/15 text-xs font-bold text-sage">
                  {i + 1}
                </span>
                <span>
                  <span className="text-sm font-medium text-espresso group-hover:text-sage">
                    {step.label}
                  </span>
                  <span className="mt-0.5 block text-xs text-muted">
                    {step.desc}
                  </span>
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}
