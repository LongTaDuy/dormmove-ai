"""Pydantic schemas for ModelRouter inputs and outputs."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.models.schemas import BudgetPreference, RoomType, TransportationMode

IntentType = Literal[
    "small_talk",
    "new_plan",
    "update_profile",
    "ask_checklist",
    "ask_budget",
    "ask_products",
    "ask_timeline",
    "ask_status",
    "unknown",
]


class ModelCallResult(BaseModel):
    model_id: str
    output: dict
    fallback_used: bool = False
    fallback_reason: str | None = None
    latency_seconds: float = 0


class LLMProfileUpdate(BaseModel):
    school_name: str | None = None
    dorm_name: str | None = None
    room_type: RoomType | None = None
    move_in_date: date | None = None
    budget_total: float | None = None
    budget_preference: BudgetPreference | None = None
    already_owned_items: list[str] = Field(default_factory=list)
    roommate_items: list[str] = Field(default_factory=list)
    dietary_or_health_needs: list[str] = Field(default_factory=list)
    climate_or_location_notes: str | None = None
    transportation_mode: TransportationMode | None = None
    restrictions: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    confidence: float = 0
    reasoning: str = ""


class LLMIntentResult(BaseModel):
    intent: IntentType = "unknown"
    confidence: float = 0
    reasoning: str = ""
