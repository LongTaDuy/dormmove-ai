"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ConnectionError } from "@/components/ConnectionError";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PlanEmptyState } from "@/components/PlanEmptyState";
import { ProductCard } from "@/components/ProductCard";
import { getProducts } from "@/lib/api";
import { usePlanResource } from "@/hooks/usePlanResource";
import { categoryLabel, formatCurrency } from "@/lib/format";

export default function ProductsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, status, errorMessage, isOffline, retry } = usePlanResource(
    sessionId,
    getProducts,
  );

  const s = data?.summary;

  return (
    <AppShell sessionId={sessionId}>
      <h1 className="page-title mb-4">Product recommendations</h1>

      <p className="mb-6 rounded-xl border border-border bg-cream/60 px-4 py-3 text-sm text-muted">
        Product data is demo seed data for now — recommendations are for
        planning only, not real checkout links.
      </p>

      {status === "loading" && <LoadingState />}
      {status === "no-session" && <PlanEmptyState kind="no-session" />}
      {status === "no-plan" && <PlanEmptyState kind="no-plan" />}
      {status === "error" && isOffline && (
        <ConnectionError message={errorMessage ?? ""} onRetry={retry} />
      )}
      {status === "error" && !isOffline && (
        <ErrorState message={errorMessage ?? ""} onRetry={retry} />
      )}

      {status === "ready" && data && s && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard label="Products" value={String(s.total_products)} />
            <StatCard label="Categories" value={String(s.category_count)} />
            <StatCard label="Avg price" value={formatCurrency(s.avg_price)} />
            <StatCard label="Avg rating" value={s.avg_rating.toFixed(1)} />
          </div>

          {Object.entries(data.categories)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([category, products]) => (
              <section key={category}>
                <div className="mb-4 flex items-center gap-2">
                  <h2 className="text-lg font-semibold text-espresso">
                    {categoryLabel(category)}
                  </h2>
                  <span className="badge border border-border bg-sage/10 text-sage">
                    {products.length} picks
                  </span>
                </div>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {products.map((p) => (
                    <ProductCard key={p.product_id} product={p} />
                  ))}
                </div>
              </section>
            ))}
        </div>
      )}
    </AppShell>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-card">
      <p className="text-xs font-medium text-muted">{label}</p>
      <p className="mt-1 text-xl font-bold text-espresso">{value}</p>
    </div>
  );
}
