"""DecisionAgent: assemble the MoveInPlan and a deterministic ScoreBreakdown.

This is a simple, explainable scoring pass. A richer scoring engine arrives in a
later milestone; the interface (a :class:`ScoreBreakdown`) stays the same.
"""

from __future__ import annotations

from datetime import date

from app.agents.base import BaseAgent
from app.models.schemas import (
    ChecklistStatus,
    ItemPriority,
    MoveInPlan,
    ScoreBreakdown,
    TransportationMode,
    Verdict,
)
from app.orchestrator.state import AgentState

# Final-score weights (sum to 1.0).
_WEIGHTS = {
    "readiness": 0.25,
    "budget_fit": 0.20,
    "dorm_compliance": 0.20,
    "logistics": 0.15,
    "product_trust": 0.20,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class DecisionAgent(BaseAgent):
    name = "DecisionAgent"

    def run(self, state: AgentState) -> AgentState:
        readiness = self._readiness_score(state)
        budget_fit = self._budget_fit_score(state)
        compliance = self._compliance_score(state)
        logistics = self._logistics_score(state)
        product_trust = self._product_trust_score(state)

        final = _clamp(
            _WEIGHTS["readiness"] * readiness
            + _WEIGHTS["budget_fit"] * budget_fit
            + _WEIGHTS["dorm_compliance"] * compliance
            + _WEIGHTS["logistics"] * logistics
            + _WEIGHTS["product_trust"] * product_trust
        )

        verdict = self._verdict(final, compliance, state)
        top_reasons = self._top_reasons(
            state, readiness, budget_fit, compliance, logistics, product_trust
        )
        missing_evidence = list(state.missing_fields)
        if not state.profile.school_name:
            missing_evidence.append("school-specific dorm rules")

        score = ScoreBreakdown(
            readiness_score=round(readiness, 3),
            budget_fit_score=round(budget_fit, 3),
            dorm_compliance_score=round(compliance, 3),
            logistics_score=round(logistics, 3),
            product_trust_score=round(product_trust, 3),
            final_move_in_score=round(final, 3),
            verdict=verdict,
            top_reasons=top_reasons,
            risk_flags=list(state.risk_flags),
            missing_evidence=missing_evidence,
        )

        plan = MoveInPlan(
            profile=state.profile,
            checklist=state.checklist,
            category_budgets=state.category_budgets,
            product_candidates=state.product_candidates,
            timeline=state.timeline,
            risk_flags=list(state.risk_flags),
            score_breakdown=score,
            final_summary=self._summary(state, score),
        )
        state.plan = plan
        state.add_trace(
            self.name,
            "built_plan",
            (
                f"Built move-in plan with verdict {verdict.value} "
                f"(score {final:.2f})."
            ),
        )
        return state

    # -- score components --------------------------------------------------

    def _readiness_score(self, state: AgentState) -> float:
        completeness = (4 - len(state.profile.missing_required_fields())) / 4
        essentials = [
            c for c in state.checklist if c.priority is ItemPriority.essential
        ]
        if essentials:
            addressed = [
                c
                for c in essentials
                if c.status
                in {
                    ChecklistStatus.already_owned,
                    ChecklistStatus.roommate_has,
                    ChecklistStatus.needed,
                }
            ]
            coverage = len(addressed) / len(essentials)
        else:
            coverage = 0.0
        return _clamp(0.5 * completeness + 0.5 * coverage)

    def _budget_fit_score(self, state: AgentState) -> float:
        budget = state.profile.budget_total
        if budget is None:
            return 0.5
        if state.estimated_cost <= 0:
            return 0.7
        if state.estimated_cost <= budget:
            return 1.0
        return _clamp(budget / state.estimated_cost)

    def _compliance_score(self, state: AgentState) -> float:
        often = sum(1 for f in state.risk_flags if f.startswith("Often prohibited"))
        check = sum(1 for f in state.risk_flags if f.startswith("Check dorm rules"))
        return _clamp(1.0 - 0.2 * often - 0.05 * check)

    def _logistics_score(self, state: AgentState) -> float:
        score = 1.0
        if any("shipping" in f.lower() or "timeline" in f.lower() for f in state.risk_flags):
            score -= 0.3
        if state.profile.transportation_mode is TransportationMode.unknown:
            score -= 0.1
        if state.profile.move_in_date is None:
            score -= 0.3
        return _clamp(score)

    def _product_trust_score(self, state: AgentState) -> float:
        products = state.product_candidates
        if not products:
            return 0.5
        total = 0.0
        for p in products:
            total += (p.rating / 5.0 + p.dorm_fit_score + p.review_quality_score) / 3
        return _clamp(total / len(products))

    # -- verdict / narrative ----------------------------------------------

    def _verdict(
        self, final: float, compliance: float, state: AgentState
    ) -> Verdict:
        has_prohibited = any(
            f.startswith("Often prohibited") for f in state.risk_flags
        )
        if has_prohibited or compliance < 0.6 or final < 0.5:
            return Verdict.HIGH_RISK
        if final >= 0.72 and not state.missing_fields:
            return Verdict.READY
        return Verdict.NEEDS_WORK

    def _top_reasons(
        self,
        state: AgentState,
        readiness: float,
        budget_fit: float,
        compliance: float,
        logistics: float,
        product_trust: float,
    ) -> list[str]:
        reasons: list[str] = []
        if readiness >= 0.8:
            reasons.append("Profile and essentials are well covered.")
        elif state.missing_fields:
            reasons.append(
                "Some required details are missing: "
                + ", ".join(state.missing_fields)
            )
        if budget_fit >= 0.99:
            reasons.append("Estimated cost fits within budget.")
        elif budget_fit < 0.8:
            reasons.append("Estimated cost is over budget.")
        if compliance < 1.0:
            reasons.append("Some items may need a dorm-rule check.")
        if logistics < 1.0:
            reasons.append("Logistics/shipping timing needs attention.")
        if product_trust >= 0.8:
            reasons.append("Recommended products are well rated.")
        return reasons[:5]

    def _summary(self, state: AgentState, score: ScoreBreakdown) -> str:
        owned = sum(
            1
            for c in state.checklist
            if c.status
            in {ChecklistStatus.already_owned, ChecklistStatus.roommate_has}
        )
        needed = sum(
            1 for c in state.checklist if c.status is ChecklistStatus.needed
        )
        parts = [
            f"Verdict: {score.verdict.value} (move-in score {score.final_move_in_score:.2f}).",
            f"{needed} items to buy, {owned} already covered.",
            f"Estimated core cost: ${state.estimated_cost:.2f}.",
        ]
        if state.risk_flags:
            parts.append(f"{len(state.risk_flags)} risk flag(s) to review.")
        return " ".join(parts)
