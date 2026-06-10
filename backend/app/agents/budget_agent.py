"""BudgetAgent: allocate budget across categories and detect overspending.

Estimates the cost of items the student still needs (status ``needed`` or
``check_rules``) and allocates the available budget across categories. Retrieved
budget tips add evidence-backed notes without changing core calculations.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.schemas import ChecklistStatus, ItemPriority
from app.orchestrator.state import AgentState
from app.rag.retriever import LocalKnowledgeRetriever, RetrievedDocument, get_retriever

# Statuses that still require spending.
_SPENDING_STATUSES = {ChecklistStatus.needed, ChecklistStatus.check_rules}
# Priorities that count toward the core budget estimate.
_CORE_PRIORITIES = {ItemPriority.essential, ItemPriority.recommended}


class BudgetAgent(BaseAgent):
    name = "BudgetAgent"

    def __init__(self, retriever: LocalKnowledgeRetriever | None = None) -> None:
        self._retriever = retriever or get_retriever()

    def run(self, state: AgentState) -> AgentState:
        needed_by_category: dict[str, float] = {}
        for item in state.checklist:
            if item.status in _SPENDING_STATUSES and item.priority in _CORE_PRIORITIES:
                needed_by_category[item.category] = (
                    needed_by_category.get(item.category, 0.0) + item.estimated_price
                )

        estimated_cost = round(sum(needed_by_category.values()), 2)
        state.estimated_cost = estimated_cost

        budget = state.profile.budget_total
        notes: list[str] = []
        flags: list[str] = []

        if budget is None:
            state.category_budgets = {
                cat: round(cost, 2) for cat, cost in needed_by_category.items()
            }
            notes.append(
                "No total budget provided; showing estimated cost per category."
            )
        elif estimated_cost <= budget:
            state.category_budgets = {
                cat: round(cost, 2) for cat, cost in needed_by_category.items()
            }
            leftover = round(budget - estimated_cost, 2)
            notes.append(
                f"Estimated core cost ${estimated_cost:.2f} fits within your "
                f"${budget:.2f} budget (about ${leftover:.2f} to spare)."
            )
        else:
            scale = budget / estimated_cost if estimated_cost else 0.0
            state.category_budgets = {
                cat: round(cost * scale, 2) for cat, cost in needed_by_category.items()
            }
            overspend = round(estimated_cost - budget, 2)
            flags.append(
                f"Overspending risk: estimated ${estimated_cost:.2f} exceeds "
                f"budget ${budget:.2f} by ${overspend:.2f}."
            )
            top_categories = sorted(
                needed_by_category, key=needed_by_category.get, reverse=True
            )[:2]
            if top_categories:
                notes.append(
                    "To stay on budget, choose cheaper options in: "
                    + ", ".join(top_categories)
                    + "; consider switching budget preference to 'cheapest'."
                )

        retrieval_query = " ".join(
            [
                state.message,
                f"budget {budget}" if budget is not None else "budget planning",
                state.profile.budget_preference.value,
                " ".join(state.profile.roommate_items),
            ]
        )
        retrieved = self._retriever.retrieve(
            retrieval_query,
            top_k=3,
            tags=["budget", "priorities", "savings", "shopping"],
        )
        state.store_retrieved_context("budget", _docs_to_dicts(retrieved))
        if retrieved:
            state.add_trace(
                self.name,
                "retrieved_budget_context",
                f"Retrieved {len(retrieved)} budget document(s).",
                evidence=_evidence_summary(retrieved),
            )
            for doc in retrieved[:2]:
                notes.append(f"Budget tip [{doc.doc_id}]: {doc.title}")

        state.budget_notes.extend(notes)
        state.add_risk_flags(flags)

        summary = (
            f"Estimated core cost ${estimated_cost:.2f} across "
            f"{len(needed_by_category)} categories."
        )
        if flags:
            summary += " Budget exceeded."
        state.add_trace(self.name, "allocated_budget", summary)
        return state


def _docs_to_dicts(documents: list[RetrievedDocument]) -> list[dict]:
    return [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "source_type": doc.source_type,
            "content": doc.content,
            "tags": doc.tags,
            "risk_level": doc.risk_level,
            "score": doc.score,
        }
        for doc in documents
    ]


def _evidence_summary(documents: list[RetrievedDocument]) -> list[dict]:
    return [
        {"doc_id": doc.doc_id, "title": doc.title, "risk_level": doc.risk_level}
        for doc in documents
    ]
