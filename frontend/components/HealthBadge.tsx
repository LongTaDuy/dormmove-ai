"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { HealthResponse } from "@/types";

export function HealthBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e) => setError(e instanceof Error ? e.message : "Unknown error"));
  }, []);

  if (error) {
    return (
      <p className="text-sm text-red-400">
        Backend unreachable: {error}. Is the API running on port 8000?
      </p>
    );
  }

  if (!health) {
    return <p className="text-sm text-white/50">Checking backend…</p>;
  }

  return (
    <div className="flex items-center gap-3">
      <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-400" />
      <span className="text-sm">
        Status <strong>{health.status}</strong> · env {health.env} · model{" "}
        {health.model_provider}
      </span>
    </div>
  );
}
