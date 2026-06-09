"""Centralized ModelRouter for optional OpenAI-backed LLM calls.

Mock mode is the default so the app runs without API keys. Profile extraction
and intent classification only — checklist, scoring, rules, and products stay
deterministic.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from app.core.config import Settings
from app.core.llm_schemas import (
    LLMIntentResult,
    LLMProfileUpdate,
    ModelCallResult,
)
from app.models.schemas import StudentMoveInProfile
from app.services.llm_telemetry import RuntimeLLMTelemetry

logger = logging.getLogger(__name__)

InvokeFn = Callable[[str, dict], Awaitable[dict]]


class ModelRouter:
    """Wrap model calls with caps, retries, timeout, and mock fallback."""

    def __init__(
        self,
        settings: Settings,
        invoke_fn: InvokeFn | None = None,
        telemetry: RuntimeLLMTelemetry | None = None,
    ) -> None:
        self.settings = settings
        self._invoke_fn = invoke_fn
        self.telemetry = telemetry or RuntimeLLMTelemetry()

    async def call(
        self,
        task_type: str,
        payload: dict,
        session_id: str | None = None,
    ) -> ModelCallResult:
        self._check_session_caps(session_id)

        model_id = (
            self.settings.llm_model
            if self.settings.model_provider == "openai"
            else "mock"
        )
        max_attempts = self.settings.llm_max_retries + 1
        last_error: Exception | None = None
        started = time.perf_counter()

        for _attempt in range(max_attempts):
            try:
                if self.settings.model_provider == "mock":
                    output = self._mock_output(task_type, payload)
                    latency = time.perf_counter() - started
                    result = ModelCallResult(
                        model_id="mock",
                        output=output,
                        latency_seconds=latency,
                    )
                    self._record_call(task_type, session_id, result)
                    return result

                output = await asyncio.wait_for(
                    self._invoke_provider(task_type, payload),
                    timeout=self.settings.llm_timeout_seconds,
                )
                latency = time.perf_counter() - started
                result = ModelCallResult(
                    model_id=model_id,
                    output=output,
                    latency_seconds=latency,
                )
                self._record_call(task_type, session_id, result)
                return result
            except Exception as exc:  # noqa: BLE001 — retry/fallback boundary
                last_error = exc
                logger.debug(
                    "ModelRouter call failed (task=%s attempt): %s",
                    task_type,
                    type(exc).__name__,
                )
                continue

        if self.settings.allow_llm_fallback:
            output = self._mock_output(task_type, payload)
            latency = time.perf_counter() - started
            result = ModelCallResult(
                model_id="mock-fallback",
                output=output,
                fallback_used=True,
                fallback_reason=str(last_error) if last_error else "unknown error",
                latency_seconds=latency,
            )
            self._record_call(task_type, session_id, result)
            return result

        raise RuntimeError(
            f"Model call failed for task '{task_type}': {last_error}"
        ) from last_error

    async def extract_profile_update(
        self,
        message: str,
        previous_profile: StudentMoveInProfile,
        session_id: str | None = None,
    ) -> LLMProfileUpdate:
        payload = {
            "message": message,
            "previous_profile": previous_profile.model_dump(mode="json"),
        }
        result = await self.call(
            task_type="profile_extraction",
            payload=payload,
            session_id=session_id,
        )
        try:
            return LLMProfileUpdate.model_validate(result.output)
        except ValidationError:
            return LLMProfileUpdate(confidence=0.0, reasoning="invalid llm output")

    async def classify_intent(
        self,
        message: str,
        previous_profile: StudentMoveInProfile | None = None,
        session_id: str | None = None,
    ) -> LLMIntentResult:
        payload: dict[str, Any] = {"message": message}
        if previous_profile is not None:
            payload["previous_profile"] = previous_profile.model_dump(mode="json")
        result = await self.call(
            task_type="intent_classification",
            payload=payload,
            session_id=session_id,
        )
        try:
            return LLMIntentResult.model_validate(result.output)
        except ValidationError:
            return LLMIntentResult(confidence=0.0, reasoning="invalid llm output")

    def snapshot_metrics(self) -> dict:
        return {
            "provider": self.settings.model_provider,
            "model": self.settings.llm_model,
            **self.telemetry.snapshot(),
        }

    # -- internals ---------------------------------------------------------

    def _check_session_caps(self, session_id: str | None) -> None:
        if not session_id:
            return
        usage = self.telemetry.session_usage(session_id)
        max_calls = self.settings.max_model_calls_per_session
        if usage["calls"] >= max_calls:
            raise RuntimeError(
                f"Session {session_id} exceeded max model calls ({max_calls})."
            )
        max_cost = self.settings.max_estimated_cost_per_session_usd
        if usage["estimatedCostUsd"] >= max_cost:
            raise RuntimeError(
                f"Session {session_id} exceeded estimated cost cap "
                f"(${max_cost:.2f})."
            )

    def _record_call(
        self,
        task_type: str,
        session_id: str | None,
        result: ModelCallResult,
    ) -> None:
        self.telemetry.record(
            task_type=task_type,
            session_id=session_id,
            latency_seconds=result.latency_seconds,
            fallback_used=result.fallback_used,
            estimated_cost_usd=self.settings.estimated_cost_per_call_usd,
        )

    async def _invoke_provider(self, task_type: str, payload: dict) -> dict:
        if self._invoke_fn is not None:
            return await self._invoke_fn(task_type, payload)
        if self.settings.model_provider == "openai":
            return await self._invoke_openai(task_type, payload)
        raise RuntimeError(
            f"Unsupported model provider: {self.settings.model_provider}"
        )

    async def _invoke_openai(self, task_type: str, payload: dict) -> dict:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        system_prompt, user_prompt = self._prompts_for_task(task_type, payload)
        model = self.settings.llm_model

        try:
            response = await client.chat.completions.create(
                model=model,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception:
            if self.settings.llm_fallback_model != model:
                response = await client.chat.completions.create(
                    model=self.settings.llm_fallback_model,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or "{}"
                return json.loads(content)
            raise

    def _prompts_for_task(self, task_type: str, payload: dict) -> tuple[str, str]:
        if task_type == "profile_extraction":
            return _PROFILE_SYSTEM_PROMPT, json.dumps(payload, default=str)
        if task_type == "intent_classification":
            return _INTENT_SYSTEM_PROMPT, json.dumps(payload, default=str)
        raise ValueError(f"Unknown task type: {task_type}")

    def _mock_output(self, task_type: str, payload: dict) -> dict:
        if task_type == "profile_extraction":
            return self._mock_profile_extraction(payload)
        if task_type == "intent_classification":
            return self._mock_intent_classification(payload)
        raise ValueError(f"Unknown task type: {task_type}")

    def _mock_profile_extraction(self, payload: dict) -> dict:
        from app.agents.profile_planner import ProfilePlannerAgent

        message = payload.get("message", "")
        previous = StudentMoveInProfile.model_validate(
            payload.get("previous_profile") or {}
        )
        profile = previous.model_copy(deep=True)
        agent = ProfilePlannerAgent()
        updated = agent.apply_deterministic_parsers(profile, message)

        confidence = 0.85 if updated else 0.35
        reasoning = (
            f"Mock extraction updated: {', '.join(updated)}."
            if updated
            else "Mock extraction found no new fields."
        )
        update = LLMProfileUpdate(
            school_name=profile.school_name,
            dorm_name=profile.dorm_name,
            room_type=(
                profile.room_type
                if profile.room_type.value != "unknown"
                else None
            ),
            move_in_date=profile.move_in_date,
            budget_total=profile.budget_total,
            budget_preference=profile.budget_preference,
            already_owned_items=list(profile.already_owned_items),
            roommate_items=list(profile.roommate_items),
            dietary_or_health_needs=list(profile.dietary_or_health_needs),
            climate_or_location_notes=profile.climate_or_location_notes,
            transportation_mode=(
                profile.transportation_mode
                if profile.transportation_mode.value != "unknown"
                else None
            ),
            restrictions=list(profile.restrictions),
            preferences=list(profile.preferences),
            confidence=confidence,
            reasoning=reasoning,
        )
        return update.model_dump(mode="json")

    def _mock_intent_classification(self, payload: dict) -> dict:
        from app.agents.concierge import ConciergeAgent

        message = payload.get("message", "")
        previous_data = payload.get("previous_profile")
        previous = (
            StudentMoveInProfile.model_validate(previous_data)
            if previous_data
            else None
        )
        route, reason = ConciergeAgent().classify(message, previous)
        result = LLMIntentResult(
            intent=route,  # type: ignore[arg-type]
            confidence=0.8,
            reasoning=reason,
        )
        return result.model_dump()


_PROFILE_SYSTEM_PROMPT = """You extract structured dorm move-in profile fields from a student message.

Rules:
- Extract ONLY facts explicitly stated by the user.
- Do NOT invent school-specific dorm rules or policies.
- Do NOT infer missing facts except the move-in year rule below.
- If a move-in date has no year, use the current calendar year when that date is still in the future; otherwise use next year.
- Understand formats like:
  "Single room, Denison University, budget 200 usd and move in date is 28th aug"
  "28th aug 2026"
  "my roommate is bringing a mini fridge"
  "I already have sheets and a desk lamp"
  "I'm flying so compact items are better"
- Leave fields null/empty when not mentioned.
- Set confidence between 0 and 1 reflecting how certain you are.
- Respond with JSON only matching this schema:
{
  "school_name": string|null,
  "dorm_name": string|null,
  "room_type": "single"|"double"|"triple"|"suite"|"apartment"|"unknown"|null,
  "move_in_date": "YYYY-MM-DD"|null,
  "budget_total": number|null,
  "budget_preference": "cheapest"|"balanced"|"premium"|null,
  "already_owned_items": string[],
  "roommate_items": string[],
  "dietary_or_health_needs": string[],
  "climate_or_location_notes": string|null,
  "transportation_mode": "flight"|"car"|"bus"|"unknown"|null,
  "restrictions": string[],
  "preferences": string[],
  "confidence": number,
  "reasoning": string
}"""

_INTENT_SYSTEM_PROMPT = """Classify the student's message intent for a dorm move-in planning assistant.

Intent options:
- small_talk
- new_plan
- update_profile
- ask_checklist
- ask_budget
- ask_products
- ask_timeline
- ask_status
- unknown

Short follow-up fragments (dates, budgets, room types, school names, transport)
should be update_profile when they add profile details.

Respond with JSON only:
{
  "intent": "<one of the options above>",
  "confidence": number between 0 and 1,
  "reasoning": string
}"""
