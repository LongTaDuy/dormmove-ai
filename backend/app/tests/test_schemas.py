"""Tests for the DormMove AI domain models and seed data."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.data.dorm_items_seed import DORM_ITEMS
from app.data.product_seed import PRODUCT_CANDIDATES
from app.models import (
    DormItem,
    ItemPriority,
    MoveInPlan,
    ProductCandidate,
    RoomType,
    ScoreBreakdown,
    StudentMoveInProfile,
)
from app.models.schemas import DormRuleRisk, ShippingUrgency


def _complete_profile() -> StudentMoveInProfile:
    return StudentMoveInProfile(
        school_name="State University",
        room_type=RoomType.double,
        move_in_date=date(2026, 8, 20),
        budget_total=600.0,
    )


def test_minimal_complete_profile():
    profile = _complete_profile()
    assert profile.is_minimally_complete is True
    assert profile.missing_required_fields() == []


def test_missing_fields():
    profile = StudentMoveInProfile()
    assert profile.is_minimally_complete is False
    missing = profile.missing_required_fields()
    assert "school_or_dorm_name" in missing
    assert "room_type" in missing
    assert "move_in_date" in missing
    assert "budget_total" in missing

    # Providing only a dorm name still satisfies the location requirement.
    partial = StudentMoveInProfile(dorm_name="West Hall")
    assert "school_or_dorm_name" not in partial.missing_required_fields()


def test_dorm_item_price_validation():
    with pytest.raises(ValidationError):
        DormItem(
            item_id="bad",
            name="Bad Item",
            category="bedding",
            priority=ItemPriority.essential,
            estimated_price_min=50,
            estimated_price_max=10,  # max < min
            dorm_rule_risk=DormRuleRisk.allowed,
            shipping_urgency=ShippingUrgency.buy_now,
            reason="invalid range",
        )

    with pytest.raises(ValidationError):
        DormItem(
            item_id="bad2",
            name="Negative Item",
            category="bedding",
            priority=ItemPriority.essential,
            estimated_price_min=-5,  # negative
            estimated_price_max=10,
            dorm_rule_risk=DormRuleRisk.allowed,
            shipping_urgency=ShippingUrgency.buy_now,
            reason="invalid min",
        )


def test_product_candidate_score_validation():
    base = dict(
        product_id="x",
        title="Test",
        category="bedding",
        price=10.0,
        rating=4.0,
        rating_count=5,
        source="DormMart",
        url="https://example.com/x",
        shipping_days=2,
        return_policy_score=0.5,
        review_quality_score=0.5,
        dorm_fit_score=0.5,
        notes="ok",
    )

    # Score above 1 is rejected.
    with pytest.raises(ValidationError):
        ProductCandidate(**{**base, "dorm_fit_score": 1.5})

    # Rating above 5 is rejected.
    with pytest.raises(ValidationError):
        ProductCandidate(**{**base, "rating": 6.0})

    # Negative price is rejected.
    with pytest.raises(ValidationError):
        ProductCandidate(**{**base, "price": -1.0})


def test_move_in_plan_with_seed_data():
    plan = MoveInPlan(
        profile=_complete_profile(),
        product_candidates=PRODUCT_CANDIDATES[:5],
        category_budgets={"bedding": 150.0, "bathroom": 80.0},
    )
    assert plan.profile.is_minimally_complete
    assert len(plan.product_candidates) == 5
    assert plan.score_breakdown.verdict.value == "NEEDS_WORK"

    # Seed catalogs load and validate.
    assert len(DORM_ITEMS) == 50
    assert len(PRODUCT_CANDIDATES) == 30
    assert all(isinstance(item, DormItem) for item in DORM_ITEMS)


def test_score_breakdown_rejects_scores_above_one():
    with pytest.raises(ValidationError):
        ScoreBreakdown(final_move_in_score=1.2)

    with pytest.raises(ValidationError):
        ScoreBreakdown(readiness_score=-0.1)
