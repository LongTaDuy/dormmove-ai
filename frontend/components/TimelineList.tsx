import type { TimelineTask } from "@/types";
import { categoryLabel, formatDate } from "@/lib/format";

export function TimelineList({ tasks }: { tasks: TimelineTask[] }) {
  const byPhase = tasks.reduce<Record<string, TimelineTask[]>>((acc, task) => {
    const list = acc[task.phase] ?? [];
    list.push(task);
    acc[task.phase] = list;
    return acc;
  }, {});

  const phases = Object.keys(byPhase);

  return (
    <div className="space-y-6">
      {phases.map((phase) => (
        <section key={phase} className="card overflow-hidden">
          <h3 className="border-b border-border bg-sage/10 px-5 py-3 text-base font-semibold text-sage">
            {categoryLabel(phase)}
          </h3>
          <ol className="relative space-y-0 p-5 pl-8 before:absolute before:bottom-5 before:left-[1.35rem] before:top-5 before:w-0.5 before:bg-border">
            {byPhase[phase].map((task) => (
              <li key={task.task_id} className="relative pb-5 last:pb-0">
                <span className="absolute -left-[1.15rem] top-1.5 z-10 h-3 w-3 rounded-full border-2 border-ivory bg-brand shadow-soft" />
                <div className="rounded-xl border border-border bg-cream/40 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <h4 className="font-semibold text-espresso">{task.title}</h4>
                    {task.due_date && (
                      <span className="rounded-full bg-ivory px-2.5 py-0.5 text-xs font-medium text-muted">
                        Due {formatDate(task.due_date)}
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-muted">
                    {task.reason}
                  </p>
                  {task.risk_flags.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {task.risk_flags.map((flag) => (
                        <span
                          key={flag}
                          className="badge border border-warning-border bg-warning-light text-warning"
                        >
                          {flag.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}
