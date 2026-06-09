"""Tests for the deterministic MoveInScoringEngine and DecisionAgent wiring."""

from datetime import date, timedelta

from app.agents.decision_agent import DecisionAgent
from app.models.schemas import (
    BudgetPreference,
    ChecklistItem,
    ChecklistStatus,
    ItemPriority,
    MoveInPlan,
    ProductCandidate,
    RoomType,
    ScoreBreakdown,
    StudentMoveInProfile,
    TimelineTask,
    TransportationMode,
    Verdict,
)
from app.orchestrator.state import AgentState
from app.services.movein_scoring import MoveInScoringEngine

ENGINE = MoveInScoringEngine()


def _profile(**overrides) -> StudentMoveInProfile:
    base = dict(
        school_name="Denison University",
        room_type=RoomType.double,
        move_in_date=date.today() + timedelta(days=45),
        budget_total=600.0,
    )
    base.update(overrides)
    return StudentMoveInProfile(**base)


def _item(
    item_id: str,
    *,
    status: ChecklistStatus,
    priority: ItemPriority = ItemPriority.essential,
    category: str = "bedding",
    price: float = 30.0,
    risk_flags: list[str] | None = None,
) -> ChecklistItem:
    return ChecklistItem(
        item_id=item_id,
        name=item_id.replace("-", " ").title(),
        category=category,
        status=status,
        priority=priority,
        estimated_price=price,
        reason="test item",
        risk_flags=risk_flags or [],
    )


def _product(
    product_id: str,
    *,
    rating: float,
    rating_count: int,
    shipping_days: int = 3,
    return_policy: float = 0.8,
    review_quality: float = 0.8,
    dorm_fit: float = 0.8,
    category: str = "bedding",
    price: float = 30.0,
) -> ProductCandidate:
    return ProductCandidate(
        product_id=product_id,
        title=product_id,
        category=category,
        price=price,
        rating=rating,
        rating_count=rating_count,
        source="TestStore",
        url="https://example.com/" + product_id,
        shipping_days=shipping_days,
        return_policy_score=return_policy,
        review_quality_score=review_quality,
        dorm_fit_score=dorm_fit,
        notes="test product",
    )


def _good_products() -> list[ProductCandidate]:
    return [
        _product("p1", rating=4.6, rating_count=500),
        _product("p2", rating=4.4, rating_count=300),
    ]


def test_high_readiness_case_scores_well():
    checklist = [
        _item("twin-xl-sheets", status=ChecklistStatus.already_owned),
        _item("pillows", status=ChecklistStatus.already_owned),
        _item("hangers", status=ChecklistStatus.already_owned),
        _item("power-strip", status=ChecklistStatus.already_owned),
        _item(
            "desk-lamp",
            status=ChecklistStatus.needed,
            priority=ItemPriority.recommended,
            price=25.0,
        ),
    ]
    score = ENGINE.score(
        profile=_profile(),
        checklist=checklist,
        category_budgets={"bedding": 90.0},
        product_candidates=_good_products(),
        timeline=[TimelineTask(task_id="t1", title="Buy", phase="shopping", reason="r")],
    )
    assert score.readiness_score >= 0.7
    assert score.final_move_in_score >= 0.78
    assert score.verdict in {Verdict.READY, Verdict.NEEDS_WORK}


def test_missing_budget_lowers_budget_fit():
    score = ENGINE.score(
        profile=_profile(budget_total=None),
        checklist=[_item("pillows", status=ChecklistStatus.needed)],
        category_budgets={},
        product_candidates=_good_products(),
        timeline=[],
    )
    assert score.budget_fit_score < 0.5
    assert "missing_budget" in score.risk_flags
    assert "budget_total" in score.missing_evidence


def test_over_budget_case_flags_and_lowers_budget_fit():
    checklist = [
        _item("a", status=ChecklistStatus.needed, price=200.0),
        _item("b", status=ChecklistStatus.needed, price=200.0),
    ]
    score = ENGINE.score(
        profile=_profile(budget_total=100.0),
        checklist=checklist,
        category_budgets={"bedding": 100.0},
        product_candidates=_good_products(),
        timeline=[],
    )
    assert "over_budget" in score.risk_flags
    assert score.budget_fit_score < 0.5


def test_check_rules_item_lowers_compliance():
    checklist = [
        _item("pillows", status=ChecklistStatus.already_owned),
        _item(
            "surge-extension-cord",
            status=ChecklistStatus.check_rules,
            category="electronics",
            risk_flags=["verify against dorm rules"],
        ),
    ]
    score = ENGINE.score(
        profile=_profile(),
        checklist=checklist,
        category_budgets={"electronics": 20.0},
        product_candidates=_good_products(),
        timeline=[],
    )
    assert score.dorm_compliance_score < 1.0
    assert "dorm_rule_check_required" in score.risk_flags


def test_late_shipping_lowers_logistics():
    score = ENGINE.score(
        profile=_profile(move_in_date=date.today() + timedelta(days=3)),
        checklist=[_item("pillows", status=ChecklistStatus.needed)],
        category_budgets={"bedding": 30.0},
        product_candidates=[_product("slow", rating=4.5, rating_count=200, shipping_days=7)],
        timeline=[],
    )
    assert "late_shipping_risk" in score.risk_flags
    assert score.logistics_score < 0.8


def test_flight_with_bulky_items_flags_risk():
    checklist = [
        _item(
            "mini-fridge",
            status=ChecklistStatus.needed,
            category="kitchen",
            priority=ItemPriority.recommended,
            price=140.0,
        )
    ]
    score = ENGINE.score(
        profile=_profile(
            transportation_mode=TransportationMode.flight,
            move_in_date=date.today() + timedelta(days=40),
        ),
        checklist=checklist,
        category_budgets={"kitchen": 140.0},
        product_candidates=[_product("fridge", rating=4.3, rating_count=200, category="kitchen")],
        timeline=[],
    )
    assert "flight_bulky_item_risk" in score.risk_flags


def test_few_reviews_scores_lower_than_many_reviews():
    high_few = _product("few", rating=5.0, rating_count=2)
    solid_many = _product("many", rating=4.6, rating_count=500)
    assert ENGINE.product_score(high_few) < ENGINE.product_score(solid_many)


def test_no_products_flags_weak_evidence():
    score = ENGINE.score(
        profile=_profile(),
        checklist=[_item("pillows", status=ChecklistStatus.needed)],
        category_budgets={"bedding": 30.0},
        product_candidates=[],
        timeline=[],
    )
    assert (
        "weak_product_evidence" in score.risk_flags
        or "product_candidates" in score.missing_evidence
    )


def test_final_score_always_in_unit_interval():
    scenarios = [
        ENGINE.score(
            profile=_profile(),
            checklist=[_item("pillows", status=ChecklistStatus.needed)],
            category_budgets={},
            product_candidates=[],
            timeline=[],
        ),
        ENGINE.score(
            profile=StudentMoveInProfile(),
            checklist=[],
            category_budgets={},
            product_candidates=[],
            timeline=[],
        ),
        ENGINE.score(
            profile=_profile(budget_preference=BudgetPreference.cheapest),
            checklist=[_item("a", status=ChecklistStatus.needed, price=999.0)],
            category_budgets={"bedding": 10.0},
            product_candidates=_good_products(),
            timeline=[],
        ),
    ]
    for score in scenarios:
        assert 0.0 <= score.final_move_in_score <= 1.0


def test_decision_agent_returns_plan_with_score_breakdown():
    state = AgentState(
        session_id="t",
        message="plan please",
        profile=_profile(),
    )
    state.checklist = [
        _item("pillows", status=ChecklistStatus.already_owned),
        _item("desk-lamp", status=ChecklistStatus.needed, priority=ItemPriority.recommended),
    ]
    state.category_budgets = {"bedding": 30.0}
    state.product_candidates = _good_products()
    state.timeline = [TimelineTask(task_id="t1", title="Buy", phase="shopping", reason="r")]
    state.estimated_cost = 30.0

    DecisionAgent().run(state)

    assert isinstance(state.plan, MoveInPlan)
    assert isinstance(state.plan.score_breakdown, ScoreBreakdown)
    assert 0.0 <= state.plan.score_breakdown.final_move_in_score <= 1.0
