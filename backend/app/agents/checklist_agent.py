"""ChecklistAgent: build a personalized checklist from the seed catalog.

Marks already-owned and roommate-provided items, flags rule-risky items for
review, and estimates each item's price as the midpoint of its min/max range.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.matching import match_any
from app.data.dorm_items_seed import DORM_ITEMS
from app.models.schemas import (
    ChecklistItem,
    ChecklistStatus,
    DormItem,
    DormRuleRisk,
)
from app.orchestrator.state import AgentState


class ChecklistAgent(BaseAgent):
    name = "ChecklistAgent"

    def run(self, state: AgentState) -> AgentState:
        profile = state.profile
        owned = profile.already_owned_items
        roommate = profile.roommate_items

        checklist: list[ChecklistItem] = []
        owned_count = 0
        roommate_count = 0
        check_rules_count = 0

        for item in DORM_ITEMS:
            status, risk_flags = self._classify_item(item, owned, roommate)
            if status is ChecklistStatus.already_owned:
                owned_count += 1
            elif status is ChecklistStatus.roommate_has:
                roommate_count += 1
            elif status is ChecklistStatus.check_rules:
                check_rules_count += 1

            checklist.append(
                ChecklistItem(
                    item_id=item.item_id,
                    name=item.name,
                    category=item.category,
                    status=status,
                    priority=item.priority,
                    estimated_price=self._midpoint(item),
                    reason=self._reason(item, status),
                    risk_flags=risk_flags,
                )
            )

        state.checklist = checklist
        state.add_trace(
            self.name,
            "generated_checklist",
            (
                f"Generated {len(checklist)} checklist items with "
                f"{owned_count + roommate_count} already owned or "
                f"roommate-provided, and {check_rules_count} needing rule review."
            ),
        )
        return state

    def _classify_item(
        self, item: DormItem, owned: list[str], roommate: list[str]
    ) -> tuple[ChecklistStatus, list[str]]:
        risk_flags: list[str] = []
        if item.dorm_rule_risk is DormRuleRisk.often_prohibited:
            risk_flags.append("often prohibited in dorms")
        elif item.dorm_rule_risk is DormRuleRisk.check_rules:
            risk_flags.append("verify against dorm rules")

        if match_any(owned, item):
            return ChecklistStatus.already_owned, risk_flags
        if match_any(roommate, item):
            return ChecklistStatus.roommate_has, risk_flags
        if item.dorm_rule_risk is not DormRuleRisk.allowed:
            return ChecklistStatus.check_rules, risk_flags
        return ChecklistStatus.needed, risk_flags

    @staticmethod
    def _midpoint(item: DormItem) -> float:
        return round((item.estimated_price_min + item.estimated_price_max) / 2, 2)

    @staticmethod
    def _reason(item: DormItem, status: ChecklistStatus) -> str:
        if status is ChecklistStatus.already_owned:
            return "You already have this, so it's marked as owned."
        if status is ChecklistStatus.roommate_has:
            return "Your roommate is bringing this; coordinate to avoid duplicates."
        if status is ChecklistStatus.check_rules:
            return f"{item.reason} Confirm this is allowed before purchasing."
        return item.reason
