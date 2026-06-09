import { HealthBadge } from "@/components/HealthBadge";

export default function Home() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-16">
      <header className="flex flex-col gap-3">
        <span className="inline-flex w-fit rounded-full bg-brand/20 px-3 py-1 text-xs font-medium text-brand">
          Scaffold
        </span>
        <h1 className="text-4xl font-bold tracking-tight">DormMove AI</h1>
        <p className="text-lg text-white/70">
          An agentic move-in planning assistant for college students. This is the
          minimal runnable frontend scaffold.
        </p>
      </header>

      <section className="rounded-xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-white/60">
          Backend connection
        </h2>
        <HealthBadge />
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        {[
          ["Personalized checklist", "Tailored to dorm constraints"],
          ["Budget-aware shopping plan", "Stays within your budget"],
          ["Product recommendations", "Category-level picks"],
          ["Move-in timeline", "Ordered, shipping-aware steps"],
          ["Risk flags", "Overspending, duplicates, prohibited items"],
          ["Explainable outputs", "Every suggestion has a reason"],
        ].map(([title, desc]) => (
          <div
            key={title}
            className="rounded-lg border border-white/10 bg-white/5 p-4"
          >
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-white/60">{desc}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
