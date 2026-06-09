import Link from "next/link";

export function EmptyState({
  title,
  message,
  actionLabel = "Go to Planner",
  actionHref = "/planner",
}: {
  title: string;
  message: string;
  actionLabel?: string;
  actionHref?: string;
}) {
  return (
    <div className="card p-8 text-center">
      <h3 className="text-lg font-semibold text-espresso">{title}</h3>
      <p className="mt-2 text-sm text-muted">{message}</p>
      <Link href={actionHref} className="btn-primary mt-6">
        {actionLabel}
      </Link>
    </div>
  );
}
