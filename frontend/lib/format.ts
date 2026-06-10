import type { Verdict } from "@/types";

export function scorePercent(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export function verdictLabel(verdict: Verdict | string): string {
  return verdict.replace(/_/g, " ");
}

export function riskLevelColor(level: string | undefined): string {
  switch (level?.toLowerCase()) {
    case "high":
      return "text-danger bg-danger-light border-danger-border";
    case "medium":
      return "text-warning bg-warning-light border-warning-border";
    case "low":
    default:
      return "text-sage bg-sage/10 border-sage/30";
  }
}

export function sourceTypeLabel(sourceType: string | undefined): string {
  if (!sourceType) return "Knowledge";
  return sourceType.replace(/_/g, " ");
}

export function verdictColor(verdict: Verdict | string): string {
  switch (verdict) {
    case "READY":
      return "text-sage bg-success-light border-success-border";
    case "HIGH_RISK":
      return "text-danger bg-danger-light border-danger-border";
    default:
      return "text-warning bg-warning-light border-warning-border";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "needed":
      return "text-brand bg-brand-light";
    case "already_owned":
      return "text-sage bg-success-light";
    case "roommate_has":
      return "text-[#5B6B8A] bg-[#E8EDF5]";
    case "check_rules":
      return "text-warning bg-warning-light";
    default:
      return "text-muted bg-cream";
  }
}

export function categoryLabel(category: string): string {
  return category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
