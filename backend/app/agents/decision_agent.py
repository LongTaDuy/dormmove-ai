"""DecisionAgent: assemble the MoveInPlan and delegate scoring.

Scoring now lives in :class:`app.services.movein_scoring.MoveInScoringEngine`.
This agent gathers the plan parts, asks the engine for a
:class:`ScoreBreakdown`, and produces a readable summary. The API response shape
is unchanged.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.schemas import ChecklistStatus, MoveInPlan, ScoreBreakdown
from app.orchestrator.state import AgentState
from app.services.movein_scoring import MoveInScoringEngine


class DecisionAgent(BaseAgent):
    name = "DecisionAgent"

    def __init__(self, scoring_engine: MoveInScoringEngine | None = None) -> None:
        self._scoring_engine = scoring_engine or MoveInScoringEngine()

    def run(self, state: AgentState) -> AgentState:
        score = self._scoring_engine.score(
            profile=state.profile,
            checklist=state.checklist,
            category_budgets=state.category_budgets,
            product_candidates=state.product_candidates,
            timeline=state.timeline,
            existing_risk_flags=state.risk_flags,
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
                f"Built move-in plan with verdict {score.verdict.value} "
                f"(score {score.final_move_in_score:.2f})."
            ),
        )
        return state

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
            f"Verdict: {score.verdict.value} "
            f"(move-in score {score.final_move_in_score:.2f}).",
            f"{needed} items to buy, {owned} already covered.",
            f"Estimated core cost: ${state.estimated_cost:.2f}.",
        ]
        if score.top_reasons:
            parts.append(score.top_reasons[0])
        if score.risk_flags:
            parts.append(f"{len(score.risk_flags)} risk flag(s) to review.")
        return " ".join(parts)
