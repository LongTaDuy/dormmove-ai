import Link from "next/link";
import { HealthBadge } from "@/components/HealthBadge";
import { DEMO_PROMPT } from "@/lib/constants";

const VALUE_PROPS = [
  {
    title: "Personalized checklist",
    desc: "50+ dorm items tailored to your room, owned gear, and roommate situation.",
    accent: "bg-brand-light text-brand",
  },
  {
    title: "Budget-aware plan",
    desc: "Category budgets and overspend warnings so you stay on track.",
    accent: "bg-sage/15 text-sage",
  },
  {
    title: "Timeline & risks",
    desc: "Shipping-aware tasks plus flags for late delivery and dorm rules.",
    accent: "bg-warning-light text-warning",
  },
];

const STEPS = [
  "Tell us your move-in details",
  "Get a checklist and budget plan",
  "Review products, timeline, and risks",
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-cream">
      <header className="sticky top-0 z-50 border-b border-border bg-ivory/95 shadow-soft backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <span className="text-lg font-bold text-espresso">
            DormMove <span className="text-brand">AI</span>
          </span>
          <HealthBadge />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12 sm:py-16">
        <section className="card overflow-hidden">
          <div className="bg-gradient-to-br from-brand-light via-ivory to-cream px-8 py-12 text-center sm:px-12 sm:py-16">
            <p className="mb-4 inline-block rounded-full border border-brand/20 bg-ivory px-4 py-1 text-xs font-semibold uppercase tracking-wide text-brand">
              Agentic move-in planning
            </p>
            <h1 className="text-4xl font-bold tracking-tight text-espresso sm:text-5xl">
              Your dorm move-in,
              <br />
              <span className="text-brand">planned with confidence</span>
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-muted">
              DormMove AI turns your dorm details, budget, and owned items into
              a personalized checklist, shopping plan, timeline, and explainable
              risk flags.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link href="/planner" className="btn-primary px-8 py-3 text-base">
                Start planning
              </Link>
              <Link href="/planner" className="btn-secondary px-8 py-3 text-base">
                View demo flow
              </Link>
            </div>
          </div>
        </section>

        <section className="mt-12 grid gap-5 sm:grid-cols-3">
          {VALUE_PROPS.map((item) => (
            <div key={item.title} className="card p-6">
              <span
                className={`inline-block rounded-lg px-2.5 py-1 text-xs font-semibold ${item.accent}`}
              >
                {item.title.split(" ")[0]}
              </span>
              <h3 className="mt-3 text-lg font-semibold text-espresso">
                {item.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                {item.desc}
              </p>
            </div>
          ))}
        </section>

        <section className="card mt-12 p-6 sm:p-8">
          <h2 className="text-lg font-semibold text-espresso">
            Try this demo prompt
          </h2>
          <p className="mt-2 text-sm text-muted">
            Paste this in the planner to see a full move-in plan in seconds.
          </p>
          <blockquote className="mt-4 rounded-xl border border-border bg-cream/60 px-4 py-4 text-sm leading-relaxed text-espresso/90">
            {DEMO_PROMPT}
          </blockquote>
          <Link href="/planner" className="btn-accent mt-5">
            Open planner with demo
          </Link>
        </section>

        <section className="card mt-12 p-8">
          <h2 className="text-center text-xl font-semibold text-espresso">
            How it works
          </h2>
          <ol className="mt-8 grid gap-8 sm:grid-cols-3">
            {STEPS.map((step, i) => (
              <li key={step} className="text-center">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-brand text-sm font-bold text-white shadow-soft">
                  {i + 1}
                </span>
                <p className="mt-4 text-sm leading-relaxed text-muted">{step}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>
    </div>
  );
}
