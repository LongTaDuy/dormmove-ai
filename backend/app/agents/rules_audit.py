"""RulesAuditAgent: flag risky or often-prohibited items.

Matches the user's message, stated items, restrictions, and the planned
checklist against the generic dorm-rule seed data. All warnings are explicitly
framed as *generic* because no school-specific rules are loaded yet.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.data.dorm_rules_seed import GENERIC_DORM_RULES
from app.models.schemas import DormRuleRisk
from app.orchestrator.state import AgentState

GENERIC_DISCLAIMER = (
    "These are generic dorm-rule warnings; confirm against your school's "
    "official housing policy."
)


class RulesAuditAgent(BaseAgent):
    name = "RulesAuditAgent"

    def run(self, state: AgentState) -> AgentState:
        profile = state.profile
        haystack_parts: list[str] = [state.message.lower()]
        haystack_parts += [s.lower() for s in profile.already_owned_items]
        haystack_parts += [s.lower() for s in profile.roommate_items]
        haystack_parts += [s.lower() for s in profile.restrictions]
        haystack_parts += [s.lower() for s in profile.preferences]
        haystack_parts += [c.name.lower() for c in state.checklist]
        haystack = " | ".join(haystack_parts)

        flags: list[str] = []
        notes: list[str] = []
        for rule in GENERIC_DORM_RULES:
            keywords = rule.get("keywords", [])
            if any(kw.lower() in haystack for kw in keywords):
                risk = rule.get("risk", DormRuleRisk.check_rules.value)
                title = rule.get("title", rule.get("rule_id", "rule"))
                warning = rule.get("warning", "")
                if risk == DormRuleRisk.often_prohibited.value:
                    flags.append(f"Often prohibited: {title}")
                elif risk == DormRuleRisk.check_rules.value:
                    flags.append(f"Check dorm rules: {title}")
                notes.append(f"{title}: {warning}")

        # Items the checklist already flagged for rule review.
        for item in state.checklist:
            if item.status.value == "check_rules":
                flag = f"Check dorm rules: {item.name}"
                if flag not in flags:
                    flags.append(flag)

        if flags and GENERIC_DISCLAIMER not in notes:
            notes.append(GENERIC_DISCLAIMER)

        state.add_risk_flags(flags)
        for note in notes:
            if note not in state.rule_notes:
                state.rule_notes.append(note)

        summary = (
            f"Flagged {len(flags)} potential rule risk(s)."
            if flags
            else "No generic dorm-rule risks detected."
        )
        state.add_trace(self.name, "audited_rules", summary)
        return state
