"""Core domain models and API schemas for DormMove AI.

These Pydantic models are the contract shared between the backend agents, the
scoring engine, the API responses, and the frontend types. They contain no
business logic beyond validation and a few derived helpers.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RoomType(str, Enum):
    single = "single"
    double = "double"
    triple = "triple"
    suite = "suite"
    apartment = "apartment"
    unknown = "unknown"


class BudgetPreference(str, Enum):
    cheapest = "cheapest"
    balanced = "balanced"
    premium = "premium"


class TransportationMode(str, Enum):
    flight = "flight"
    car = "car"
    bus = "bus"
    unknown = "unknown"


class ItemPriority(str, Enum):
    essential = "essential"
    recommended = "recommended"
    optional = "optional"


class DormRuleRisk(str, Enum):
    allowed = "allowed"
    check_rules = "check_rules"
    often_prohibited = "often_prohibited"


class ShippingUrgency(str, Enum):
    buy_now = "buy_now"
    can_wait = "can_wait"
    buy_after_arrival = "buy_after_arrival"


class ChecklistStatus(str, Enum):
    needed = "needed"
    already_owned = "already_owned"
    roommate_has = "roommate_has"
    skip = "skip"
    check_rules = "check_rules"


class Verdict(str, Enum):
    READY = "READY"
    NEEDS_WORK = "NEEDS_WORK"
    HIGH_RISK = "HIGH_RISK"


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class StudentMoveInProfile(BaseModel):
    school_name: str | None = None
    dorm_name: str | None = None
    room_type: RoomType = RoomType.unknown
    move_in_date: date | None = None
    budget_total: float | None = None
    budget_preference: BudgetPreference = BudgetPreference.balanced
    already_owned_items: list[str] = Field(default_factory=list)
    roommate_items: list[str] = Field(default_factory=list)
    dietary_or_health_needs: list[str] = Field(default_factory=list)
    climate_or_location_notes: str | None = None
    transportation_mode: TransportationMode = TransportationMode.unknown
    restrictions: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)

    @property
    def is_minimally_complete(self) -> bool:
        """True only when the minimum fields needed to plan are present."""
        has_location = bool(self.school_name or self.dorm_name)
        return (
            has_location
            and self.room_type is not RoomType.unknown
            and self.move_in_date is not None
            and self.budget_total is not None
        )

    def missing_required_fields(self) -> list[str]:
        """Return the list of required fields still missing from the profile."""
        missing: list[str] = []
        if not (self.school_name or self.dorm_name):
            missing.append("school_or_dorm_name")
        if self.room_type is RoomType.unknown:
            missing.append("room_type")
        if self.move_in_date is None:
            missing.append("move_in_date")
        if self.budget_total is None:
            missing.append("budget_total")
        return missing


# ---------------------------------------------------------------------------
# Catalog / planning models
# ---------------------------------------------------------------------------


class DormItem(BaseModel):
    item_id: str
    name: str
    category: str
    priority: ItemPriority
    estimated_price_min: float = Field(ge=0)
    estimated_price_max: float = Field(ge=0)
    dorm_rule_risk: DormRuleRisk
    shipping_urgency: ShippingUrgency
    reason: str

    @model_validator(mode="after")
    def _check_price_range(self) -> "DormItem":
        if self.estimated_price_max < self.estimated_price_min:
            raise ValueError(
                "estimated_price_max must be >= estimated_price_min"
            )
        return self


class ChecklistItem(BaseModel):
    item_id: str
    name: str
    category: str
    status: ChecklistStatus
    priority: ItemPriority
    estimated_price: float = Field(ge=0)
    reason: str
    risk_flags: list[str] = Field(default_factory=list)


class ProductCandidate(BaseModel):
    product_id: str
    title: str
    category: str
    price: float = Field(ge=0)
    rating: float = Field(ge=0, le=5)
    rating_count: int = Field(ge=0)
    source: str
    url: str
    shipping_days: int = Field(ge=0)
    return_policy_score: float = Field(ge=0, le=1)
    review_quality_score: float = Field(ge=0, le=1)
    dorm_fit_score: float = Field(ge=0, le=1)
    notes: str


class TimelineTask(BaseModel):
    task_id: str
    title: str
    phase: str
    due_date: date | None = None
    reason: str
    risk_flags: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    readiness_score: float = Field(default=0, ge=0, le=1)
    budget_fit_score: float = Field(default=0, ge=0, le=1)
    dorm_compliance_score: float = Field(default=0, ge=0, le=1)
    logistics_score: float = Field(default=0, ge=0, le=1)
    product_trust_score: float = Field(default=0, ge=0, le=1)
    final_move_in_score: float = Field(default=0, ge=0, le=1)
    verdict: Verdict = Verdict.NEEDS_WORK
    top_reasons: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class MoveInPlan(BaseModel):
    profile: StudentMoveInProfile
    checklist: list[ChecklistItem] = Field(default_factory=list)
    category_budgets: dict[str, float] = Field(default_factory=dict)
    product_candidates: list[ProductCandidate] = Field(default_factory=list)
    timeline: list[TimelineTask] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    final_summary: str = ""


# ---------------------------------------------------------------------------
# Chat / session API models
# ---------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    title: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    profile: StudentMoveInProfile
    plan: MoveInPlan | None = None
    missing_fields: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    trace: list[dict] = Field(default_factory=list)


class SessionSummary(BaseModel):
    session_id: str
    title: str = "DormMove Plan"
    created_at: str | None = None
    updated_at: str | None = None
    latest_score: float | None = None
    latest_verdict: str | None = None
    message_count: int = 0
    has_plan: bool = False
    # Legacy / convenience fields kept for existing consumers.
    school_name: str | None = None
    dorm_name: str | None = None
    move_in_date: date | None = None
    verdict: Verdict = Verdict.NEEDS_WORK


class SessionSnapshotResponse(BaseModel):
    session_id: str
    title: str = "DormMove Plan"
    created_at: str = ""
    updated_at: str = ""
    profile: StudentMoveInProfile
    messages: list[dict] = Field(default_factory=list)
    latest_plan: MoveInPlan | None = None
    latest_score: ScoreBreakdown | None = None


class ChecklistSummary(BaseModel):
    total: int = 0
    needed: int = 0
    already_owned: int = 0
    roommate_has: int = 0
    check_rules: int = 0
    estimated_remaining_cost: float = 0.0


class ChecklistEnvelopeResponse(BaseModel):
    session_id: str
    checklist: list[ChecklistItem] = Field(default_factory=list)
    summary: ChecklistSummary = Field(default_factory=ChecklistSummary)


class ProductRecommendationsSummary(BaseModel):
    total_products: int = 0
    category_count: int = 0
    avg_price: float = 0.0
    avg_rating: float = 0.0


class ProductRecommendationsEnvelopeResponse(BaseModel):
    session_id: str
    categories: dict[str, list[ProductCandidate]] = Field(default_factory=dict)
    summary: ProductRecommendationsSummary = Field(
        default_factory=ProductRecommendationsSummary
    )


class TimelineSummary(BaseModel):
    total_tasks: int = 0
    phases: list[str] = Field(default_factory=list)
    risk_flag_count: int = 0


class TimelineEnvelopeResponse(BaseModel):
    session_id: str
    timeline: list[TimelineTask] = Field(default_factory=list)
    summary: TimelineSummary = Field(default_factory=TimelineSummary)


class RiskFlagCount(BaseModel):
    flag: str
    count: int


class RuntimeMetricsResponse(BaseModel):
    session_count: int = 0
    message_count: int = 0
    plan_snapshot_count: int = 0
    average_final_move_in_score: float | None = None
    verdict_counts: dict[str, int] = Field(default_factory=dict)
    most_common_risk_flags: list[RiskFlagCount] = Field(default_factory=list)
    generated_at: datetime
