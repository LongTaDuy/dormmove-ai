"use client";

import { useMemo, useState } from "react";
import type { ChecklistItem, ChecklistStatus } from "@/types";
import { categoryLabel, formatCurrency, statusColor } from "@/lib/format";

const FILTERS: { value: "all" | ChecklistStatus; label: string }[] = [
  { value: "all", label: "All" },
  { value: "needed", label: "Needed" },
  { value: "already_owned", label: "Owned" },
  { value: "roommate_has", label: "Roommate" },
  { value: "check_rules", label: "Check rules" },
];

export function ChecklistTable({ items }: { items: ChecklistItem[] }) {
  const [filter, setFilter] = useState<"all" | ChecklistStatus>("all");

  const filtered = useMemo(
    () =>
      filter === "all" ? items : items.filter((i) => i.status === filter),
    [items, filter],
  );

  const grouped = useMemo(() => {
    const map = new Map<string, ChecklistItem[]>();
    for (const item of filtered) {
      const list = map.get(item.category) ?? [];
      list.push(item);
      map.set(item.category, list);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [filtered]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setFilter(f.value)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-brand/30 ${
              filter === f.value
                ? "bg-brand text-white shadow-soft"
                : "border border-border bg-ivory text-muted hover:border-border-dark hover:text-espresso"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {grouped.map(([category, catItems]) => (
        <div key={category} className="card overflow-hidden">
          <h3 className="border-b border-border bg-brand-light/50 px-5 py-3 text-base font-semibold text-brand-dark">
            {categoryLabel(category)}
            <span className="ml-2 text-sm font-normal text-muted">
              ({catItems.length})
            </span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-border bg-cream/40 text-xs uppercase tracking-wide text-muted">
                  <th className="px-5 py-3 font-semibold">Item</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Priority</th>
                  <th className="px-5 py-3 font-semibold">Est. price</th>
                  <th className="px-5 py-3 font-semibold">Reason</th>
                </tr>
              </thead>
              <tbody>
                {catItems.map((item) => (
                  <tr
                    key={item.item_id}
                    className="border-b border-border/60 last:border-0 hover:bg-cream/30"
                  >
                    <td className="px-5 py-4 font-medium text-espresso">
                      {item.name}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`badge ${statusColor(item.status)}`}
                      >
                        {item.status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-5 py-4 capitalize text-muted">
                      {item.priority}
                    </td>
                    <td className="px-5 py-4 font-medium text-espresso">
                      {formatCurrency(item.estimated_price)}
                    </td>
                    <td className="max-w-sm px-5 py-4 text-muted">
                      {item.reason}
                      {item.risk_flags.length > 0 && (
                        <span className="mt-1 block text-xs text-warning">
                          {item.risk_flags.join(" · ")}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <p className="py-12 text-center text-muted">
          No items match this filter.
        </p>
      )}
    </div>
  );
}
