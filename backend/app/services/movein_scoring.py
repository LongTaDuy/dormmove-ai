"""Deterministic move-in readiness scoring engine.

``MoveInScoringEngine`` turns a plan's parts (profile, checklist, budgets,
products, timeline) into an explainable :class:`ScoreBreakdown`. It is fully
deterministic: no LLM, no network, no randomness. All scores are clamped to the
0..1 range and risk flags use normalized snake_case identifiers.
"""

from __future__ import annotations

import math
from datetime import date

from app.models.schemas import (
    BudgetPreference,
    ChecklistItem,
    ChecklistStatus,
    ItemPriority,
    ProductCandidate,
    ScoreBreakdown,
    StudentMoveInProfile,
    TimelineTask,
    TransportationMode,
    Verdict,
)

# Final-score component weights (sum to 1.0).
WEIGHTS = {
    "readiness": 0.25,
    "budget_fit": 0.25,
    "dorm_compliance": 0.20,
    "logistics": 0.15,
    "product_trust": 0.15,
}

# Statuses that still require buying something.
_SPENDING_STATUSES = {ChecklistStatus.needed, ChecklistStatus.check_rules}

# Bayesian rating prior.
_PRIOR_MEAN = 4.1  # C: assumed average rating across the catalog
_PRIOR_STRENGTH = 50  # m: how many prior reviews the prior is worth
_CONFIDENCE_SCALE = 500  # reviews needed to reach full rating-count confidence

# Generic high-risk rule terms (substring match, lowercased).
_HIGH_RISK_TERMS = (
    "candle",
    "hot plate",
    "hotplate",
    "space heater",
    "air fryer",
    "toaster oven",
    "alcohol",
    "pet",
    "router",
    "incense",
    "halogen",
)

# Categories whose items are bulky/awkward to fly with.
_BULKY_CATEGORIES = {"kitchen", "storage", "decor"}

# Risk flags that block a READY verdict.
_SEVERE_FLAGS = {
    "over_budget",
    "late_shipping_risk",
    "generic_prohibited_item_warning",
    "flight_bulky_item_risk",
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class MoveInScoringEngine:
    """Computes a deterministic, explainable move-in readiness score."""

    def score(
        self,
        *,
        profile: StudentMoveInProfile,
        checklist: list[ChecklistItem],
        category_budgets: dict[str, float],
        product_candidates: list[ProductCandidate],
        timeline: list[TimelineTask],
        existing_risk_flags: list[str] | None = None,
    ) -> ScoreBreakdown:
        existing_risk_flags = existing_risk_flags or []
        risk_flags: list[str] = []
        missing_evidence: list[str] = []

        estimated_total_cost = self._estimated_total_cost(checklist)

        readiness = self._readiness_score(
            profile, checklist, category_budgets, timeline
        )
        budget_fit = self._budget_fit_score(
            profile, estimated_total_cost, category_budgets, risk_flags, missing_evidence
        )
        compliance = self._dorm_compliance_score(
            profile, checklist, existing_risk_flags, risk_flags
        )
        logistics = self._logistics_score(
            profile, checklist, product_candidates, timeline, risk_flags, missing_evidence
        )
        product_trust = self._product_trust_score(
            product_candidates, risk_flags, missing_evidence
        )

        final = _clamp(
            WEIGHTS["readiness"] * readiness
            + WEIGHTS["budget_fit"] * budget_fit
            + WEIGHTS["dorm_compliance"] * compliance
            + WEIGHTS["logistics"] * logistics
            + WEIGHTS["product_trust"] * product_trust
        )

        # Unresolved essentials are a readiness risk worth surfacing.
        if self._essentials_needed(checklist) > 0:
            self._add_flag(risk_flags, "unresolved_essential_items")

        for field_name in profile.missing_required_fields():
            if field_name not in missing_evidence:
                missing_evidence.append(field_name)

        verdict = self._verdict(final, compliance, budget_fit, logistics, risk_flags)
        top_reasons = self._top_reasons(
            readiness=readiness,
            budget_fit=budget_fit,
            compliance=compliance,
            logistics=logistics,
            product_trust=product_trust,
            risk_flags=risk_flags,
        )

        return ScoreBreakdown(
            readiness_score=round(readiness, 3),
            budget_fit_score=round(budget_fit, 3),
            dorm_compliance_score=round(compliance, 3),
            logistics_score=round(logistics, 3),
            product_trust_score=round(product_trust, 3),
            final_move_in_score=round(final, 3),
            verdict=verdict,
            top_reasons=top_reasons,
            risk_flags=risk_flags,
            missing_evidence=missing_evidence,
        )

    # -- shared helpers ----------------------------------------------------

    @staticmethod
    def _estimated_total_cost(checklist: list[ChecklistItem]) -> float:
        return round(
            sum(c.estimated_price for c in checklist if c.status in _SPENDING_STATUSES),
            2,
        )

    @staticmethod
    def _essentials_needed(checklist: list[ChecklistItem]) -> int:
        return sum(
            1
            for c in checklist
            if c.priority is ItemPriority.essential
            and c.status is ChecklistStatus.needed
        )

    @staticmethod
    def _add_flag(flags: list[str], flag: str) -> None:
        if flag not in flags:
            flags.append(flag)

    # -- component scores --------------------------------------------------

    def _readiness_score(
        self,
        profile: StudentMoveInProfile,
        checklist: list[ChecklistItem],
        category_budgets: dict[str, float],
        timeline: list[TimelineTask],
    ) -> float:
        score = 0.35 if profile.is_minimally_complete else 0.0

        essentials = [
            c for c in checklist if c.priority is ItemPriority.essential
        ]
        if essentials:
            resolved = sum(
                1 for c in essentials if c.status is not ChecklistStatus.needed
            )
            coverage = resolved / len(essentials)
        else:
            coverage = 0.0
        score += 0.45 * coverage

        if timeline:
            score += 0.10
        if category_budgets:
            score += 0.10

        essentials_needed = self._essentials_needed(checklist)
        score -= min(0.15, 0.02 * essentials_needed)

        return _clamp(score)

    def _budget_fit_score(
        self,
        profile: StudentMoveInProfile,
        estimated_total_cost: float,
        category_budgets: dict[str, float],
        risk_flags: list[str],
        missing_evidence: list[str],
    ) -> float:
        budget = profile.budget_total
        if budget is None or budget <= 0:
            self._add_flag(risk_flags, "missing_budget")
            if "budget_total" not in missing_evidence:
                missing_evidence.append("budget_total")
            return 0.3

        if estimated_total_cost <= 0:
            return 0.7

        ratio = estimated_total_cost / budget
        cheapest = profile.budget_preference is BudgetPreference.cheapest

        if ratio <= 1.0:
            score = 1.0
        elif cheapest:
            # Stricter: even a small overage matters for the cheapest preference.
            self._add_flag(risk_flags, "over_budget")
            score = 0.45 if ratio <= 1.05 else _clamp(budget / estimated_total_cost) * 0.8
        elif ratio <= 1.10:
            score = 0.6
        else:
            self._add_flag(risk_flags, "over_budget")
            score = _clamp(budget / estimated_total_cost)

        # Slight reduction when there is no per-category plan to spend against.
        if not category_budgets:
            score *= 0.95

        return _clamp(score)

    def _dorm_compliance_score(
        self,
        profile: StudentMoveInProfile,
        checklist: list[ChecklistItem],
        existing_risk_flags: list[str],
        risk_flags: list[str],
    ) -> float:
        score = 1.0
        needs_rule_check = False
        has_prohibited = False

        for item in checklist:
            if item.status is ChecklistStatus.check_rules:
                score -= 0.05
                needs_rule_check = True
            if any("prohibit" in rf.lower() for rf in item.risk_flags):
                score -= 0.10
                has_prohibited = True

        haystack = " | ".join(
            [s.lower() for s in profile.restrictions]
            + [c.name.lower() for c in checklist]
            + [f.lower() for f in existing_risk_flags]
        )
        for flag in existing_risk_flags:
            low = flag.lower()
            if "prohibit" in low:
                has_prohibited = True
            if "check dorm rules" in low or "rule" in low:
                needs_rule_check = True

        seen_terms: set[str] = set()
        for term in _HIGH_RISK_TERMS:
            if term in haystack and term not in seen_terms:
                score -= 0.15
                seen_terms.add(term)
                has_prohibited = True

        if needs_rule_check:
            self._add_flag(risk_flags, "dorm_rule_check_required")
        if has_prohibited:
            self._add_flag(risk_flags, "generic_prohibited_item_warning")

        return _clamp(score)

    def _logistics_score(
        self,
        profile: StudentMoveInProfile,
        checklist: list[ChecklistItem],
        product_candidates: list[ProductCandidate],
        timeline: list[TimelineTask],
        risk_flags: list[str],
        missing_evidence: list[str],
    ) -> float:
        if profile.move_in_date is None:
            self._add_flag(risk_flags, "missing_move_in_date")
            if "move_in_date" not in missing_evidence:
                missing_evidence.append("move_in_date")
            return 0.3

        days_until = (profile.move_in_date - date.today()).days
        score = 1.0

        max_ship = max(
            (p.shipping_days for p in product_candidates), default=0
        )
        if days_until < 0:
            self._add_flag(risk_flags, "late_shipping_risk")
            score -= 0.5
        elif days_until <= 7 and max_ship > days_until:
            self._add_flag(risk_flags, "late_shipping_risk")
            score -= 0.35
        elif days_until <= 7:
            score -= 0.10

        if profile.transportation_mode is TransportationMode.flight:
            bulky_needed = [
                c
                for c in checklist
                if c.status in _SPENDING_STATUSES
                and c.category in _BULKY_CATEGORIES
            ]
            if bulky_needed:
                self._add_flag(risk_flags, "flight_bulky_item_risk")
                score -= 0.15

        if timeline:
            score += 0.05

        return _clamp(score)

    def _product_trust_score(
        self,
        product_candidates: list[ProductCandidate],
        risk_flags: list[str],
        missing_evidence: list[str],
    ) -> float:
        if not product_candidates:
            self._add_flag(risk_flags, "weak_product_evidence")
            if "product_candidates" not in missing_evidence:
                missing_evidence.append("product_candidates")
            return 0.4

        total = sum(self.product_score(p) for p in product_candidates)
        avg = total / len(product_candidates)

        if avg < 0.5:
            self._add_flag(risk_flags, "weak_product_evidence")

        return _clamp(avg)

    @staticmethod
    def product_score(product: ProductCandidate) -> float:
        """Conservative per-product trust score in 0..1.

        Uses a Bayesian average so a 5.0-star item with very few reviews cannot
        outrank a slightly-lower item with many reviews.
        """
        r = product.rating
        v = product.rating_count
        bayes = (v * r + _PRIOR_STRENGTH * _PRIOR_MEAN) / (v + _PRIOR_STRENGTH)
        normalized_bayes = (bayes - 1) / 4
        rating_count_confidence = min(
            1.0, math.log1p(v) / math.log1p(_CONFIDENCE_SCALE)
        )
        return _clamp(
            0.40 * normalized_bayes
            + 0.20 * rating_count_confidence
            + 0.15 * product.return_policy_score
            + 0.15 * product.review_quality_score
            + 0.10 * product.dorm_fit_score
        )

    # -- verdict / narrative ----------------------------------------------

    @staticmethod
    def _verdict(
        final: float,
        compliance: float,
        budget_fit: float,
        logistics: float,
        risk_flags: list[str],
    ) -> Verdict:
        if compliance < 0.55 or budget_fit < 0.45 or logistics < 0.45:
            return Verdict.HIGH_RISK
        severe = any(flag in _SEVERE_FLAGS for flag in risk_flags)
        if final >= 0.78 and not severe:
            return Verdict.READY
        return Verdict.NEEDS_WORK

    @staticmethod
    def _top_reasons(
        *,
        readiness: float,
        budget_fit: float,
        compliance: float,
        logistics: float,
        product_trust: float,
        risk_flags: list[str],
    ) -> list[str]:
        reasons: list[str] = []

        if readiness >= 0.75:
            reasons.append("Profile has the required move-in basics.")
        elif readiness < 0.5:
            reasons.append("Profile or essential items are incomplete.")

        if budget_fit >= 0.9:
            reasons.append("Estimated checklist cost is within budget.")
        elif "over_budget" in risk_flags:
            reasons.append("Estimated checklist cost is over budget.")
        elif "missing_budget" in risk_flags:
            reasons.append("No budget set, so cost fit can't be confirmed.")

        if "dorm_rule_check_required" in risk_flags:
            reasons.append("Several items require dorm-rule confirmation.")
        if "generic_prohibited_item_warning" in risk_flags:
            reasons.append("Some items are commonly prohibited in dorms.")
        if "late_shipping_risk" in risk_flags:
            reasons.append("Some recommended products may arrive too late.")
        if "flight_bulky_item_risk" in risk_flags:
            reasons.append("Bulky items are hard to fly with; buy them locally.")

        if product_trust >= 0.7:
            reasons.append("Recommended products have solid review depth.")
        elif "weak_product_evidence" in risk_flags:
            reasons.append("Product recommendations have limited review depth.")

        # Ensure at least three reasons for a useful explanation.
        fallback = [
            "Move-in plan generated from your current details.",
            "Add more details to sharpen the recommendations.",
            "Confirm dorm specifics for the most accurate plan.",
        ]
        i = 0
        while len(reasons) < 3 and i < len(fallback):
            if fallback[i] not in reasons:
                reasons.append(fallback[i])
            i += 1

        return reasons[:5]
