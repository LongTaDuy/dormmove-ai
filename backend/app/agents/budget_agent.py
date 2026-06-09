"""BudgetAgent: allocate budget across categories and detect overspending.

Estimates the cost of items the student still needs (status ``needed`` or
``check_rules``) and allocates the available budget across categories. If the
estimate exceeds the budget, it scales allocations down and emits an
overspending risk flag plus a concrete suggestion.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.schemas import ChecklistStatus, ItemPriority
from app.orchestrator.state import AgentState

# Statuses that still require spending.
_SPENDING_STATUSES = {ChecklistStatus.needed, ChecklistStatus.check_rules}
# Priorities that count toward the core budget estimate.
_CORE_PRIORITIES = {ItemPriority.essential, ItemPriority.recommended}


class BudgetAgent(BaseAgent):
    name = "BudgetAgent"

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
