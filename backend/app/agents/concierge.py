"""ConciergeAgent: classify the user's message intent and pick a route.

Rule-based intent detection with optional LLM classification when provider is
not mock. The route drives which downstream agents run.
"""

from __future__ import annotations

import re

from app.agents.base import BaseAgent
from app.core.async_utils import run_sync_async
from app.core.config import Settings, get_settings
from app.core.model_router import ModelRouter
from app.models.schemas import StudentMoveInProfile
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
_FOLLOW_UP_DATE = re.compile(
    r"\b(\d{1,2}(?:st|nd|rd|th)?\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    r"|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}",
    re.IGNORECASE,
)
_FOLLOW_UP_BUDGET = re.compile(r"^\$?\s?\d{2,5}(?:\.\d{1,2})?\s*(usd|dollars)?$", re.IGNORECASE)
_FOLLOW_UP_ROOM = re.compile(
    r"^\s*(single|double|triple|suite|apartment|apt)\s*(room)?\s*$",
    re.IGNORECASE,
)
_FOLLOW_UP_TRANSPORT = re.compile(
    r"\b(i will fly|i'm flying|flying|fly to campus|taking a flight)\b",
    re.IGNORECASE,
)
_KNOWN_SCHOOL_FRAGMENTS = (
    "denison",
    "ohio state",
    "michigan",
    "nyu",
    "ucla",
    "berkeley",
    "stanford",
    "purdue",
)

_LLM_CONFIDENCE_THRESHOLD = 0.7


class ConciergeAgent(BaseAgent):
    name = "ConciergeAgent"

    def __init__(
        self,
        model_router: ModelRouter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._model_router = model_router
        self._settings = settings or get_settings()

    def run(self, state: AgentState) -> AgentState:
        route, reason = self.classify(state.message, state.profile)

        if self._model_router and self._settings.model_provider != "mock":
            try:
                intent = run_sync_async(
                    self._model_router.classify_intent(
                        message=state.message,
                        previous_profile=state.profile,
                        session_id=state.session_id,
                    )
                )
                if intent.confidence >= _LLM_CONFIDENCE_THRESHOLD:
                    route = intent.intent
                    reason = intent.reasoning or "llm intent classification"
            except Exception as exc:  # noqa: BLE001 — keep deterministic route
                reason = f"{reason} (llm skipped: {exc})"

        state.route = route
        state.route_reason = reason
        state.add_trace(
            self.name,
            "routed_message",
            f"Routed message to '{route}' ({reason}).",
        )
        return state

    def classify(
        self,
        message: str,
        profile: StudentMoveInProfile | None = None,
    ) -> tuple[str, str]:
        text = message.lower().strip()
        if not text:
            return "unknown", "empty message"

        if _NEW_PLAN_SIGNALS.search(text):
            return "new_plan", "describes a move-in scenario"

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

        if _PLAN_SIGNALS.search(text):
            if re.search(r"\b(also|update|change|actually|add|forgot|by the way)\b", text):
                return "update_profile", "adds/updates profile details"
            return "new_plan", "describes a move-in scenario"

        if _SMALL_TALK.search(text):
            return "small_talk", "greeting or pleasantry"

        if profile is not None and not profile.is_minimally_complete:
            if len(message.strip()) <= 64:
                fragment_reason = self._follow_up_reason(message, text, profile)
                if fragment_reason:
                    return "update_profile", fragment_reason

        return "unknown", "no clear intent matched"

    def _follow_up_reason(
        self,
        message: str,
        text: str,
        profile: StudentMoveInProfile,
    ) -> str | None:
        if profile.move_in_date is None and _FOLLOW_UP_DATE.search(message):
            return "short move-in date follow-up"
        if profile.budget_total is None and _FOLLOW_UP_BUDGET.match(message.strip()):
            return "short budget follow-up"
        if profile.room_type.value == "unknown" and _FOLLOW_UP_ROOM.match(message.strip()):
            return "short room type follow-up"
        if (
            profile.transportation_mode.value == "unknown"
            and _FOLLOW_UP_TRANSPORT.search(text)
        ):
            return "short transportation follow-up"
        if not (profile.school_name or profile.dorm_name):
            if any(school in text for school in _KNOWN_SCHOOL_FRAGMENTS):
                return "short school name follow-up"
            if re.fullmatch(r"[a-z][a-z\s]{2,30}", text) and len(text.split()) <= 3:
                return "short school name follow-up"
        return None
