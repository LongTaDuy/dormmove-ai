"""Shared mutable state passed between agents.

The orchestrator runs a sequence of agents, each receiving and mutating a single
:class:`AgentState`. Keeping intermediate results on a plain dataclass (rather
than a Pydantic model) avoids re-validation on every hop and makes the state
easy to map onto a LangGraph ``TypedDict`` state later.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.schemas import (
    ChecklistItem,
    MoveInPlan,
    ProductCandidate,
    StudentMoveInProfile,
    TimelineTask,
)


@dataclass
class AgentState:
    """Working state for a single chat turn."""

    session_id: str
    message: str
    profile: StudentMoveInProfile

    # Routing (set by ConciergeAgent)
    route: str = "unknown"
    route_reason: str = ""

    # Planning artifacts
    checklist: list[ChecklistItem] = field(default_factory=list)
    category_budgets: dict[str, float] = field(default_factory=dict)
    budget_notes: list[str] = field(default_factory=list)
    product_candidates: list[ProductCandidate] = field(default_factory=list)
    product_scores: dict[str, float] = field(default_factory=dict)
    timeline: list[TimelineTask] = field(default_factory=list)

    # Risk / rules
    risk_flags: list[str] = field(default_factory=list)
    rule_notes: list[str] = field(default_factory=list)

    # Local RAG retrieval (keyed by agent domain: rules, checklist, budget, timeline)
    retrieved_context: dict[str, list[dict]] = field(default_factory=dict)

    # Derived numbers
    estimated_cost: float = 0.0

    # Outputs
    missing_fields: list[str] = field(default_factory=list)
    plan: MoveInPlan | None = None
    reply: str = ""
    trace: list[dict] = field(default_factory=list)

    def add_trace(
        self,
        agent: str,
        action: str,
        summary: str,
        evidence: list[dict] | None = None,
    ) -> None:
        """Append a structured trace entry describing what an agent did."""
        entry: dict = {"agent": agent, "action": action, "summary": summary}
        if evidence:
            entry["evidence"] = evidence
        self.trace.append(entry)

    def store_retrieved_context(
        self, domain: str, documents: list[dict]
    ) -> None:
        """Persist retrieved knowledge snippets for a planning domain."""
        if documents:
            self.retrieved_context[domain] = documents

    def add_risk_flags(self, flags: list[str]) -> None:
        """Add risk flags, de-duplicating while preserving order."""
        for flag in flags:
            if flag not in self.risk_flags:
                self.risk_flags.append(flag)
