"""ConciergeAgent: classify the user's message intent and pick a route.

Rule-based intent detection. The route drives which downstream agents run. A
ModelRouter-backed classifier can replace ``_classify`` later without changing
the rest of the pipeline.
"""

from __future__ import annotations

import re

from app.agents.base import BaseAgent
from app.orchestrator.state import AgentState

# Ordered routes; the first matching rule wins.
ROUTES = (
    "small_talk",
    "new_plan",
    "update_profile",
    "ask_checklist",
    "ask_budget",
    "ask_products",
    "ask_timeline",
    "ask_status",
    "unknown",
)

_SMALL_TALK = re.compile(
    r"\b(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening)|how are you)\b",
    re.IGNORECASE,
)
# Strong signals that the user is describing a full move-in scenario. These take
# priority over question intents so a rich first message becomes a new plan.
_NEW_PLAN_SIGNALS = re.compile(
    r"\b(moving in|move[- ]?in|moving into|i('?m| am) moving|freshman year|"
    r"starting (college|school)|new (dorm|student))\b",
    re.IGNORECASE,
)
_PLAN_SIGNALS = re.compile(
    r"\b(dorm|college|university|freshman|budget|checklist|pack|packing|"
    r"room|roommate)\b",
    re.IGNORECASE,
)


class ConciergeAgent(BaseAgent):
    name = "ConciergeAgent"

    def run(self, state: AgentState) -> AgentState:
        route, reason = self._classify(state.message)
        state.route = route
        state.route_reason = reason
        state.add_trace(
            self.name,
            "routed_message",
            f"Routed message to '{route}' ({reason}).",
        )
        return state

    def _classify(self, message: str) -> tuple[str, str]:
        text = message.lower().strip()
        if not text:
            return "unknown", "empty message"

        # A rich move-in description is a new plan even if it mentions shipping,
        # budget, etc. in passing.
        if _NEW_PLAN_SIGNALS.search(text):
            return "new_plan", "describes a move-in scenario"

        # Specific question intents take priority over generic planning signals.
        if re.search(r"\bchecklist\b|what (do|should) i (need|buy|bring)", text):
            return "ask_checklist", "asks about what to buy/bring"
        if re.search(r"\bbudget\b.*\?|how much|afford|overspend|spend(ing)?\b", text):
            return "ask_budget", "asks about budget or cost"
        if re.search(r"\bproduct|recommend|which (one|brand)|what should i buy\b", text):
            return "ask_products", "asks for product recommendations"
        if re.search(r"\btimeline|when should i|schedule|deadline|ship(ping)?\b", text):
            return "ask_timeline", "asks about timing/timeline"
        if re.search(r"\b(status|ready|am i ready|how am i doing|verdict)\b", text):
            return "ask_status", "asks about readiness/status"

        # New plan vs. profile update.
        if _PLAN_SIGNALS.search(text):
            if re.search(r"\b(also|update|change|actually|add|forgot|by the way)\b", text):
                return "update_profile", "adds/updates profile details"
            return "new_plan", "describes a move-in scenario"

        if _SMALL_TALK.search(text):
            return "small_talk", "greeting or pleasantry"

        return "unknown", "no clear intent matched"
