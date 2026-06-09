"use client";

import { useEffect, useState } from "react";
import { getRuntimeMetrics, isNetworkError } from "@/lib/api";
import { scorePercent } from "@/lib/format";
import type { RuntimeMetricsResponse } from "@/types";

export function RuntimeMetricsCard() {
  const [metrics, setMetrics] = useState<RuntimeMetricsResponse | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    getRuntimeMetrics()
      .then(setMetrics)
      .catch((e) => {
        if (isNetworkError(e)) setOffline(true);
      });
  }, []);

  if (offline) {
    return (
      <div className="card border-border bg-cream/50 p-5 text-center">
        <p className="text-sm text-muted">Backend offline — stats unavailable</p>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="card animate-pulse p-5">
        <div className="h-4 w-32 rounded bg-border" />
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-12 rounded-lg bg-border/60" />
          ))}
        </div>
      </div>
    );
  }

  const stats = [
    { label: "Sessions", value: String(metrics.session_count) },
    { label: "Messages", value: String(metrics.message_count) },
    { label: "Plans", value: String(metrics.plan_snapshot_count) },
    {
      label: "Avg score",
      value:
        metrics.average_final_move_in_score != null
          ? scorePercent(metrics.average_final_move_in_score)
          : "—",
    },
  ];

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-espresso">Local demo stats</h2>
      <p className="mt-1 text-sm text-muted">
        Live counts from your SQLite session store on this machine.
      </p>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map((s) => (
          <div
            key={s.label}
            className="rounded-xl border border-border bg-cream/50 px-3 py-3 text-center"
          >
            <p className="text-xs font-medium text-muted">{s.label}</p>
            <p className="mt-1 text-xl font-bold text-brand">{s.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
