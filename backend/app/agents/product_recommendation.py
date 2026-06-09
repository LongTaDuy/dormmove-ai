"""ProductRecommendationAgent: rank seeded products per needed category.

Uses only the local ``PRODUCT_CANDIDATES`` seed data (no scraping, no APIs).
A ``product_score`` (0..1) is computed per candidate according to the student's
budget preference and stored on the state for the trace, leaving the
``ProductCandidate`` schema unchanged.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.data.product_seed import PRODUCT_CANDIDATES
from app.models.schemas import (
    BudgetPreference,
    ChecklistStatus,
    ProductCandidate,
)
from app.orchestrator.state import AgentState

# Statuses that warrant a product suggestion.
_NEEDED_STATUSES = {ChecklistStatus.needed, ChecklistStatus.check_rules}
_MAX_PER_CATEGORY = 2


class ProductRecommendationAgent(BaseAgent):
    name = "ProductRecommendationAgent"

    def run(self, state: AgentState) -> AgentState:
        needed_categories = {
            item.category
            for item in state.checklist
            if item.status in _NEEDED_STATUSES
        }
        preference = state.profile.budget_preference

        by_category: dict[str, list[ProductCandidate]] = {}
        for product in PRODUCT_CANDIDATES:
            if product.category in needed_categories:
                by_category.setdefault(product.category, []).append(product)

        recommendations: list[ProductCandidate] = []
        for category, products in by_category.items():
            prices = [p.price for p in products] or [0.0]
            max_price = max(prices) or 1.0
            scored = [
                (self._score(p, preference, max_price), p) for p in products
            ]
            scored.sort(key=lambda pair: pair[0], reverse=True)
            for score, product in scored[:_MAX_PER_CATEGORY]:
                state.product_scores[product.product_id] = round(score, 3)
                recommendations.append(product)

        state.product_candidates = recommendations
        state.add_trace(
            self.name,
            "recommended_products",
            (
                f"Recommended {len(recommendations)} products across "
                f"{len(by_category)} categories using '{preference.value}' "
                "preference."
            ),
        )
        return state

    @staticmethod
    def _score(
        product: ProductCandidate,
        preference: BudgetPreference,
        max_price: float,
    ) -> float:
        cheapness = 1.0 - (product.price / max_price) if max_price else 0.0
        rating_norm = product.rating / 5.0
        popularity = min(product.rating_count / 10000.0, 1.0)

        if preference is BudgetPreference.cheapest:
            return (
                0.6 * cheapness
                + 0.2 * rating_norm
                + 0.2 * product.dorm_fit_score
            )
        if preference is BudgetPreference.premium:
            return (
                0.4 * product.dorm_fit_score
                + 0.3 * rating_norm
                + 0.3 * product.return_policy_score
            )
        # balanced
        return (
            0.3 * rating_norm
            + 0.25 * product.dorm_fit_score
            + 0.2 * popularity
            + 0.15 * cheapness
            + 0.1 * product.return_policy_score
        )
