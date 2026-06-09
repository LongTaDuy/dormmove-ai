import { Suspense } from "react";
import { LoadingState } from "@/components/LoadingState";
import { AppShell } from "@/components/AppShell";
import { PlannerClient } from "./PlannerClient";

export default function PlannerPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <LoadingState message="Loading planner…" />
        </AppShell>
      }
    >
      <PlannerClient />
    </Suspense>
  );
}
