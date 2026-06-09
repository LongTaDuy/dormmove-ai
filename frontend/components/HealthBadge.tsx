"use client";

import { useEffect, useState } from "react";
import { health } from "@/lib/api";
import type { HealthResponse } from "@/types";

export function HealthBadge() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    health()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Unreachable"));
  }, []);

  if (error) {
    return (
      <span className="badge border border-danger-border bg-danger-light text-danger">
        <span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-danger" />
        Backend offline
      </span>
    );
  }

  if (!data) {
    return (
      <span className="badge border border-border bg-cream text-muted">
        <span className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-muted/40" />
        Checking…
      </span>
    );
  }

  return (
    <span className="badge border border-success-border bg-success-light text-sage">
      <span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-sage" />
      API {data.status}
    </span>
  );
}
