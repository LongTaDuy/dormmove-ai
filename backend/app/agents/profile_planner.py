"""ProfilePlannerAgent: extract/update the StudentMoveInProfile from a message.

All parsing here is deterministic (regex + keyword lookups) so the app works
with no LLM. A ModelRouter can later be used to fill gaps the parser misses.
"""

from __future__ import annotations

import re
from datetime import date

from app.agents.base import BaseAgent
from app.core.async_utils import run_sync_async
from app.core.config import Settings, get_settings
from app.core.llm_schemas import LLMProfileUpdate
from app.core.model_router import ModelRouter
from app.models.schemas import (
    BudgetPreference,
    RoomType,
    StudentMoveInProfile,
    TransportationMode,
)
from app.orchestrator.state import AgentState

# Known schools by lowercase keyword -> canonical name. Extend as needed.
KNOWN_SCHOOLS: dict[str, str] = {
    "denison": "Denison University",
    "ohio state": "Ohio State University",
    "michigan": "University of Michigan",
    "nyu": "New York University",
    "ucla": "UCLA",
    "berkeley": "UC Berkeley",
    "stanford": "Stanford University",
    "purdue": "Purdue University",
}

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_ROOM_TYPES = {
    "single": RoomType.single,
    "double": RoomType.double,
    "triple": RoomType.triple,
    "suite": RoomType.suite,
    "apartment": RoomType.apartment,
    "apt": RoomType.apartment,
}

_ARTICLES = ("a ", "an ", "the ", "some ", "my ")


class ProfilePlannerAgent(BaseAgent):
    name = "ProfilePlannerAgent"

    def __init__(
        self,
        model_router: ModelRouter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._model_router = model_router
        self._settings = settings or get_settings()

    def run(self, state: AgentState) -> AgentState:
        profile = state.profile
        message = state.message
        updated = self.apply_deterministic_parsers(profile, message)

        llm_note = ""
        if self._model_router and self._settings.model_provider != "mock":
            try:
                llm_update = run_sync_async(
                    self._model_router.extract_profile_update(
                        message=message,
                        previous_profile=profile,
                        session_id=state.session_id,
                    )
                )
                merged = merge_llm_profile_update(profile, llm_update)
                updated = list(dict.fromkeys(updated + merged))
                if merged:
                    llm_note = (
                        f" LLM merge ({llm_update.confidence:.2f}): "
                        f"{', '.join(merged)}."
                    )
            except Exception as exc:  # noqa: BLE001 — continue with baseline
                llm_note = f" LLM extraction skipped: {exc}."

        state.missing_fields = profile.missing_required_fields()

        summary = (
            f"Updated fields: {', '.join(updated)}."
            if updated
            else "No new profile fields extracted."
        )
        summary += llm_note
        if state.missing_fields:
            summary += f" Still missing: {', '.join(state.missing_fields)}."
        state.add_trace(self.name, "updated_profile", summary)
        return state

    def apply_deterministic_parsers(
        self, profile: StudentMoveInProfile, message: str
    ) -> list[str]:
        """Run regex/keyword parsers and return names of fields that changed."""
        updated: list[str] = []
        self._parse_school(message, profile, updated)
        self._parse_dorm(message, profile, updated)
        self._parse_room_type(message, profile, updated)
        self._parse_move_in_date(message, profile, updated)
        self._parse_budget(message, profile, updated)
        self._parse_budget_preference(message, profile, updated)
        self._parse_owned_items(message, profile, updated)
        self._parse_roommate_items(message, profile, updated)
        self._parse_transportation(message, profile, updated)
        self._parse_restrictions(message, profile, updated)
        self._parse_preferences(message, profile, updated)
        return updated

    # -- individual field parsers ------------------------------------------

    def _parse_school(self, msg: str, profile, updated: list[str]) -> None:
        if profile.school_name:
            return
        low = msg.lower()
        for keyword, canonical in KNOWN_SCHOOLS.items():
            if keyword in low:
                profile.school_name = canonical
                updated.append("school_name")
                return
        # Generic "<Name> University/College" capture.
        m = re.search(
            r"\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\s(University|College)\b",
            msg,
        )
        if m:
            profile.school_name = f"{m.group(1)} {m.group(2)}"
            updated.append("school_name")

    def _parse_dorm(self, msg: str, profile, updated: list[str]) -> None:
        if profile.dorm_name:
            return
        m = re.search(r"\b([A-Z][a-zA-Z]+)\s(Hall|House|Tower|Residence)\b", msg)
        if m:
            profile.dorm_name = f"{m.group(1)} {m.group(2)}"
            updated.append("dorm_name")

    def _parse_room_type(self, msg: str, profile, updated: list[str]) -> None:
        if profile.room_type is not RoomType.unknown:
            return
        low = msg.lower()
        for keyword, room in _ROOM_TYPES.items():
            if re.search(rf"\b{keyword}\b", low):
                profile.room_type = room
                updated.append("room_type")
                return

    def _parse_move_in_date(self, msg: str, profile, updated: list[str]) -> None:
        if profile.move_in_date is not None:
            return
        parsed = self._extract_date(msg)
        if parsed:
            profile.move_in_date = parsed
            updated.append("move_in_date")

    def _parse_budget(self, msg: str, profile, updated: list[str]) -> None:
        if profile.budget_total is not None:
            return
        stripped = msg.strip()
        # Short follow-up like "$500" or "500".
        if re.fullmatch(r"\$?\s?(\d{2,5}(?:\.\d{1,2})?)", stripped):
            profile.budget_total = float(re.sub(r"[^\d.]", "", stripped))
            updated.append("budget_total")
            return
        # "$650" or "650 dollars" or "budget is 650" / "budget of 650".
        m = re.search(r"\$\s?(\d{2,5}(?:\.\d{1,2})?)", msg)
        if not m:
            m = re.search(
                r"budget[^\d]{0,15}(\d{2,5}(?:\.\d{1,2})?)", msg, re.IGNORECASE
            )
        if not m:
            m = re.search(r"(\d{2,5}(?:\.\d{1,2})?)\s*(dollars|usd)\b", msg, re.IGNORECASE)
        if m:
            profile.budget_total = float(m.group(1))
            updated.append("budget_total")

    def _parse_budget_preference(self, msg: str, profile, updated: list[str]) -> None:
        low = msg.lower()
        pref: BudgetPreference | None = None
        if re.search(r"\b(cheapest|cheap|budget[- ]friendly|save money|frugal)\b", low):
            pref = BudgetPreference.cheapest
        elif re.search(r"\b(premium|high[- ]end|best quality|top quality|luxury)\b", low):
            pref = BudgetPreference.premium
        elif re.search(r"\b(balanced|mix of price|good value)\b", low):
            pref = BudgetPreference.balanced
        if pref and profile.budget_preference != pref:
            profile.budget_preference = pref
            updated.append("budget_preference")

    def _parse_owned_items(self, msg: str, profile, updated: list[str]) -> None:
        items: list[str] = []
        for m in re.finditer(
            r"\bi (?:already )?(?:have|own|got|brought|packed)\b(.+?)(?:[.;!?]|$)",
            msg,
            re.IGNORECASE,
        ):
            items.extend(self._split_items(m.group(1)))
        if items:
            added = self._extend_unique(profile.already_owned_items, items)
            if added:
                updated.append("already_owned_items")

    def _parse_roommate_items(self, msg: str, profile, updated: list[str]) -> None:
        items: list[str] = []
        for m in re.finditer(
            r"\broommate\b[^.;!?]*?\b(?:is bringing|bringing|brings|has|will bring|"
            r"is getting|getting)\b(.+?)(?:[.;!?]|$)",
            msg,
            re.IGNORECASE,
        ):
            items.extend(self._split_items(m.group(1)))
        if items:
            added = self._extend_unique(profile.roommate_items, items)
            if added:
                updated.append("roommate_items")

    def _parse_transportation(self, msg: str, profile, updated: list[str]) -> None:
        if profile.transportation_mode is not TransportationMode.unknown:
            return
        low = msg.lower()
        mode: TransportationMode | None = None
        if re.search(r"\b(fly|flying|flight|plane|airport)\b", low):
            mode = TransportationMode.flight
        elif re.search(r"\b(driv(e|ing)|car|road trip)\b", low):
            mode = TransportationMode.car
        elif re.search(r"\bbus|coach|greyhound\b", low):
            mode = TransportationMode.bus
        if mode:
            profile.transportation_mode = mode
            updated.append("transportation_mode")

    def _parse_restrictions(self, msg: str, profile, updated: list[str]) -> None:
        found: list[str] = []
        for m in re.finditer(
            r"\b(?:no|not allowed|can't have|cannot have|prohibit(?:ed|s)?)\b\s+"
            r"([a-zA-Z][a-zA-Z \-]{2,30})",
            msg,
            re.IGNORECASE,
        ):
            found.append(m.group(1).strip().lower())
        if found:
            added = self._extend_unique(profile.restrictions, found)
            if added:
                updated.append("restrictions")

    def _parse_preferences(self, msg: str, profile, updated: list[str]) -> None:
        prefs: list[str] = []
        low = msg.lower()
        if re.search(r"\bcompact|space[- ]saving|small\b", low):
            prefs.append("compact items")
        if re.search(r"\blightweight|light\b", low):
            prefs.append("lightweight items")
        if re.search(r"\bship(ping)? to campus|ship to (the )?dorm\b", low):
            prefs.append("ship to campus")
        if re.search(r"\beco|sustainable|reusable\b", low):
            prefs.append("eco-friendly")
        if prefs:
            added = self._extend_unique(profile.preferences, prefs)
            if added:
                updated.append("preferences")

    # -- helpers -----------------------------------------------------------

    def _extract_date(self, msg: str) -> date | None:
        today = date.today()

        # Day-first form: "28th aug 2026", "28 aug" (check before month-first).
        m = re.search(
            r"\b(\d{1,2})(?:st|nd|rd|th)?\s+"
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
            r"(?:\.?\s*(\d{4}))?",
            msg,
            re.IGNORECASE,
        )
        if m:
            day = int(m.group(1))
            month = _MONTHS[m.group(2).lower()[:3]]
            year = int(m.group(3)) if m.group(3) else None
            return self._build_date(year, month, day, today)

        # Month-name form: "August 24", "Aug 24th, 2026".
        m = re.search(
            r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+"
            r"(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(\d{4}))?",
            msg,
            re.IGNORECASE,
        )
        if m:
            month = _MONTHS[m.group(1).lower()[:3]]
            day = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else None
            return self._build_date(year, month, day, today)

        # Numeric form: "8/24" or "8-24-2026".
        m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", msg)
        if m:
            month = int(m.group(1))
            day = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else None
            if year is not None and year < 100:
                year += 2000
            if 1 <= month <= 12:
                return self._build_date(year, month, day, today)
        return None

    @staticmethod
    def _build_date(
        year: int | None, month: int, day: int, today: date
    ) -> date | None:
        try:
            if year is None:
                candidate = date(today.year, month, day)
                if candidate < today:
                    candidate = date(today.year + 1, month, day)
                return candidate
            return date(year, month, day)
        except ValueError:
            return None

    @staticmethod
    def _split_items(chunk: str) -> list[str]:
        chunk = re.sub(r"\band\b", ",", chunk, flags=re.IGNORECASE)
        parts = [p.strip(" .,;") for p in chunk.split(",")]
        items: list[str] = []
        for part in parts:
            part = part.strip().lower()
            for article in _ARTICLES:
                if part.startswith(article):
                    part = part[len(article):]
            part = part.strip()
            if part and len(part) <= 40:
                items.append(part)
        return items

    @staticmethod
    def _extend_unique(target: list[str], new_items: list[str]) -> list[str]:
        existing = {x.lower() for x in target}
        added: list[str] = []
        for item in new_items:
            if item.lower() not in existing:
                target.append(item)
                existing.add(item.lower())
                added.append(item)
        return added


def merge_llm_profile_update(
    profile: StudentMoveInProfile,
    update: LLMProfileUpdate,
    min_confidence: float = 0.5,
) -> list[str]:
    """Merge high-confidence LLM fields; never overwrite non-null with null."""
    if update.confidence < min_confidence:
        return []

    changed: list[str] = []

    if update.school_name and not profile.school_name:
        profile.school_name = update.school_name
        changed.append("school_name")
    if update.dorm_name and not profile.dorm_name:
        profile.dorm_name = update.dorm_name
        changed.append("dorm_name")
    if update.room_type is not None and profile.room_type is RoomType.unknown:
        profile.room_type = update.room_type
        changed.append("room_type")
    if update.move_in_date is not None and profile.move_in_date is None:
        profile.move_in_date = update.move_in_date
        changed.append("move_in_date")
    if update.budget_total is not None and profile.budget_total is None:
        profile.budget_total = update.budget_total
        changed.append("budget_total")
    if (
        update.budget_preference is not None
        and profile.budget_preference is BudgetPreference.balanced
        and update.budget_preference is not BudgetPreference.balanced
    ):
        profile.budget_preference = update.budget_preference
        changed.append("budget_preference")
    if update.climate_or_location_notes and not profile.climate_or_location_notes:
        profile.climate_or_location_notes = update.climate_or_location_notes
        changed.append("climate_or_location_notes")
    if (
        update.transportation_mode is not None
        and profile.transportation_mode is TransportationMode.unknown
    ):
        profile.transportation_mode = update.transportation_mode
        changed.append("transportation_mode")

    for field_name in (
        "already_owned_items",
        "roommate_items",
        "dietary_or_health_needs",
        "restrictions",
        "preferences",
    ):
        new_items = getattr(update, field_name)
        if new_items:
            added = ProfilePlannerAgent._extend_unique(
                getattr(profile, field_name), new_items
            )
            if added:
                changed.append(field_name)

    return changed
