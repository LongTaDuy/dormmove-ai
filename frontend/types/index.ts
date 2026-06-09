// Mirrors backend Pydantic schemas (app/models/schemas.py)

export type RoomType =
  | "single"
  | "double"
  | "triple"
  | "suite"
  | "apartment"
  | "unknown";

export type BudgetPreference = "cheapest" | "balanced" | "premium";

export type TransportationMode = "flight" | "car" | "bus" | "unknown";

export type ItemPriority = "essential" | "recommended" | "optional";

export type ChecklistStatus =
  | "needed"
  | "already_owned"
  | "roommate_has"
  | "skip"
  | "check_rules";

export type Verdict = "READY" | "NEEDS_WORK" | "HIGH_RISK";

export interface HealthResponse {
  status: string;
  env: string;
  model_provider: string;
}

export interface StudentMoveInProfile {
  school_name: string | null;
  dorm_name: string | null;
  room_type: RoomType;
  move_in_date: string | null;
  budget_total: number | null;
  budget_preference: BudgetPreference;
  already_owned_items: string[];
  roommate_items: string[];
  dietary_or_health_needs: string[];
  climate_or_location_notes: string | null;
  transportation_mode: TransportationMode;
  restrictions: string[];
  preferences: string[];
}

export interface ChecklistItem {
  item_id: string;
  name: string;
  category: string;
  status: ChecklistStatus;
  priority: ItemPriority;
  estimated_price: number;
  reason: string;
  risk_flags: string[];
}

export interface ProductCandidate {
  product_id: string;
  title: string;
  category: string;
  price: number;
  rating: number;
  rating_count: number;
  source: string;
  url: string;
  shipping_days: number;
  return_policy_score: number;
  review_quality_score: number;
  dorm_fit_score: number;
  notes: string;
}

export interface TimelineTask {
  task_id: string;
  title: string;
  phase: string;
  due_date: string | null;
  reason: string;
  risk_flags: string[];
}

export interface ScoreBreakdown {
  readiness_score: number;
  budget_fit_score: number;
  dorm_compliance_score: number;
  logistics_score: number;
  product_trust_score: number;
  final_move_in_score: number;
  verdict: Verdict;
  top_reasons: string[];
  risk_flags: string[];
  missing_evidence: string[];
}

export interface MoveInPlan {
  profile: StudentMoveInProfile;
  checklist: ChecklistItem[];
  category_budgets: Record<string, number>;
  product_candidates: ProductCandidate[];
  timeline: TimelineTask[];
  risk_flags: string[];
  score_breakdown: ScoreBreakdown;
  final_summary: string;
}

export interface CreateSessionResponse {
  session_id: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  profile: StudentMoveInProfile;
  plan: MoveInPlan | null;
  missing_fields: string[];
  risk_flags: string[];
  trace: TraceEntry[];
}

export interface TraceEntry {
  agent: string;
  action: string;
  summary: string;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  created_at: string | null;
  updated_at: string | null;
  latest_score: number | null;
  latest_verdict: string | null;
  message_count: number;
  has_plan: boolean;
  school_name?: string | null;
  dorm_name?: string | null;
  move_in_date?: string | null;
  verdict?: Verdict;
}

export interface SessionMessage {
  message_id: string;
  role: string;
  content: string;
  created_at: string;
  meta: Record<string, unknown>;
}

export interface SessionSnapshotResponse {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  profile: StudentMoveInProfile;
  messages: SessionMessage[];
  latest_plan: MoveInPlan | null;
  latest_score: ScoreBreakdown | null;
}

export interface ChecklistSummary {
  total: number;
  needed: number;
  already_owned: number;
  roommate_has: number;
  check_rules: number;
  estimated_remaining_cost: number;
}

export interface ChecklistEnvelopeResponse {
  session_id: string;
  checklist: ChecklistItem[];
  summary: ChecklistSummary;
}

export interface ProductRecommendationsSummary {
  total_products: number;
  category_count: number;
  avg_price: number;
  avg_rating: number;
}

export interface ProductRecommendationsEnvelopeResponse {
  session_id: string;
  categories: Record<string, ProductCandidate[]>;
  summary: ProductRecommendationsSummary;
}

export interface TimelineSummary {
  total_tasks: number;
  phases: string[];
  risk_flag_count: number;
}

export interface TimelineEnvelopeResponse {
  session_id: string;
  timeline: TimelineTask[];
  summary: TimelineSummary;
}

export interface RiskFlagCount {
  flag: string;
  count: number;
}

export interface RuntimeMetricsResponse {
  session_count: number;
  message_count: number;
  plan_snapshot_count: number;
  average_final_move_in_score: number | null;
  verdict_counts: Record<string, number>;
  most_common_risk_flags: RiskFlagCount[];
  generated_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
