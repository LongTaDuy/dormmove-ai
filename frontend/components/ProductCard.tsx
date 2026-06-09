import type { ProductCandidate } from "@/types";
import { formatCurrency } from "@/lib/format";

export function ProductCard({ product }: { product: ProductCandidate }) {
  return (
    <div className="card flex flex-col p-5 transition hover:shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h4 className="text-base font-semibold leading-snug text-espresso">
          {product.title}
        </h4>
        <span className="badge border border-border bg-cream text-muted">
          {product.source}
        </span>
      </div>

      <p className="mt-3 text-2xl font-bold text-brand">
        {formatCurrency(product.price)}
      </p>

      <div className="mt-3 flex flex-wrap gap-3 text-sm text-muted">
        <span className="font-medium text-espresso">
          ★ {product.rating.toFixed(1)}
        </span>
        <span>({product.rating_count.toLocaleString()} reviews)</span>
        <span>Ships in {product.shipping_days} days</span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
        <ScorePill label="Returns" value={product.return_policy_score} />
        <ScorePill label="Reviews" value={product.review_quality_score} />
        <ScorePill label="Dorm fit" value={product.dorm_fit_score} />
      </div>

      {product.notes && (
        <p className="mt-4 flex-1 text-sm leading-relaxed text-muted">
          {product.notes}
        </p>
      )}

      <button
        type="button"
        disabled
        title="Demo seed data only — no real checkout"
        className="mt-5 w-full cursor-not-allowed rounded-xl border border-dashed border-border bg-cream/50 py-2.5 text-sm font-medium text-muted"
      >
        Open product (demo data)
      </button>
    </div>
  );
}

function ScorePill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-cream/60 px-2 py-2">
      <p className="text-muted">{label}</p>
      <p className="mt-0.5 font-semibold text-espresso">
        {Math.round(value * 100)}%
      </p>
    </div>
  );
}
