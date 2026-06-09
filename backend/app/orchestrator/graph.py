"""Rule-based orchestrator that runs agents in sequence.

This intentionally mirrors a LangGraph flow: a shared state object is threaded
through nodes (agents), and routing decides which nodes execute. To switch to
LangGraph later, wrap each agent's ``run`` as a node and reuse :class:`AgentState`
as the graph state; the public :meth:`Orchestrator.run_turn` contract stays the
same.
"""

from __future__ import annotations

from app.agents import (
    BudgetAgent,
    ChecklistAgent,
    ConciergeAgent,
    DecisionAgent,
    MoveInTimelineAgent,
    ProductRecommendationAgent,
    ProfilePlannerAgent,
    RulesAuditAgent,
)
from app.core.config import Settings, get_settings
from app.core.model_router import ModelRouter
from app.models.schemas import StudentMoveInProfile
from app.orchestrator.state import AgentState

# Routes that trigger (re)building a plan.
PLANNING_ROUTES = {
    "new_plan",
    "update_profile",
    "ask_checklist",
    "ask_budget",
    "ask_products",
    "ask_timeline",
    "ask_status",
}


class Orchestrator:
    """Coordinates the rule-based agent pipeline for one chat turn."""

    def __init__(
        self,
        settings: Settings | None = None,
        model_router: ModelRouter | None = None,
    ) -> None:
        settings = settings or get_settings()
        router = model_router or ModelRouter(settings)
        self.concierge = ConciergeAgent(model_router=router, settings=settings)
        self.profile_planner = ProfilePlannerAgent(
            model_router=router, settings=settings
        )
        self.checklist_agent = ChecklistAgent()
        self.rules_audit = RulesAuditAgent()
        self.budget_agent = BudgetAgent()
        self.product_agent = ProductRecommendationAgent()
        self.timeline_agent = MoveInTimelineAgent()
        self.decision_agent = DecisionAgent()

    def run_turn(
        self, session_id: str, message: str, profile: StudentMoveInProfile | None
    ) -> AgentState:
        working_profile = (
            profile.model_copy(deep=True)
            if profile is not None
            else StudentMoveInProfile()
        )
        state = AgentState(
            session_id=session_id, message=message, profile=working_profile
        )

        # Always classify intent and refresh the profile from the message.
        self.concierge.run(state)
        self.profile_planner.run(state)

        if state.route in PLANNING_ROUTES and state.profile.is_minimally_complete:
            self._run_planning_pipeline(state)
            state.reply = self._plan_reply(state)
        elif state.route in PLANNING_ROUTES:
            state.reply = self._follow_up_reply(state)
        elif state.route == "small_talk":
            state.reply = (
                "Hi! I'm DormMove AI. Tell me about your move-in (school, room "
                "type, move-in date, and budget) and I'll build your plan."
            )
        else:
            state.reply = (
                "I can help you plan your dorm move-in. Share your school, room "
                "type, move-in date, budget, and anything you already own."
            )

        return state

    def _run_planning_pipeline(self, state: AgentState) -> None:
        # Checklist before rules audit so the audit can inspect planned items.
        self.checklist_agent.run(state)
        self.rules_audit.run(state)
        self.budget_agent.run(state)
        self.product_agent.run(state)
        self.timeline_agent.run(state)
        self.decision_agent.run(state)

    def _plan_reply(self, state: AgentState) -> str:
        plan = state.plan
        if plan is None:  # defensive; pipeline always sets it here
            return "Your plan is ready."
        score = plan.score_breakdown
        lines = [
            f"Here's your move-in plan ({score.verdict.value}, "
            f"score {score.final_move_in_score:.2f}).",
            plan.final_summary,
        ]
        if state.risk_flags:
            lines.append("Top risks: " + "; ".join(state.risk_flags[:3]))
        return " ".join(lines)

    def _follow_up_reply(self, state: AgentState) -> str:
        missing = state.missing_fields
        pretty = {
            "school_or_dorm_name": "your school or dorm name",
            "room_type": "your room type (single, double, suite...)",
            "move_in_date": "your move-in date",
            "budget_total": "your total budget",
        }
        wanted = [pretty.get(m, m) for m in missing]
        return (
            "Great start! To build your full plan, I still need "
            + ", ".join(wanted)
            + "."
        )


def create_orchestrator(
    settings: Settings | None = None,
    model_router: ModelRouter | None = None,
) -> Orchestrator:
    """Build an orchestrator wired to settings and optional ModelRouter."""
    return Orchestrator(settings=settings, model_router=model_router)


# Module-level singleton; agents are stateless so this is safe to reuse.
orchestrator = create_orchestrator()
