"""Tests for LLM-assisted profile extraction and merge behavior."""

from __future__ import annotations

from datetime import date

from app.agents.profile_planner import (
    ProfilePlannerAgent,
    merge_llm_profile_update,
)
from app.core.config import Settings


def _settings(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)

from app.core.llm_schemas import LLMProfileUpdate
from app.core.model_router import ModelRouter
from app.models.schemas import RoomType, StudentMoveInProfile
from app.orchestrator.graph import Orchestrator
from app.orchestrator.state import AgentState


class _FakeModelRouter(ModelRouter):
    """Inject deterministic LLM profile updates without calling OpenAI."""

    def __init__(self, update: LLMProfileUpdate) -> None:
        super().__init__(_settings(model_provider="openai"))
        self._update = update

    async def extract_profile_update(self, message, previous_profile, session_id=None):
        return self._update


def test_profile_planner_merges_fake_llm_update():
    profile = StudentMoveInProfile()
    update = LLMProfileUpdate(
        school_name="Denison University",
        room_type=RoomType.double,
        budget_total=650.0,
        confidence=0.9,
        reasoning="test injection",
    )
    agent = ProfilePlannerAgent(
        model_router=_FakeModelRouter(update),
        settings=_settings(model_provider="openai"),
    )
    state = AgentState(
        session_id="merge-test",
        message="ignored by fake router",
        profile=profile,
    )
    agent.run(state)

    assert state.profile.school_name == "Denison University"
    assert state.profile.room_type is RoomType.double
    assert state.profile.budget_total == 650.0


def test_llm_null_fields_do_not_overwrite_existing_profile():
    profile = StudentMoveInProfile(
        school_name="Existing College",
        room_type=RoomType.single,
        budget_total=400.0,
        move_in_date=date(2026, 8, 20),
    )
    update = LLMProfileUpdate(
        school_name="Denison University",
        room_type=RoomType.double,
        budget_total=900.0,
        move_in_date=date(2026, 8, 28),
        confidence=0.95,
    )
    changed = merge_llm_profile_update(profile, update)

    assert profile.school_name == "Existing College"
    assert profile.room_type is RoomType.single
    assert profile.budget_total == 400.0
    assert profile.move_in_date == date(2026, 8, 20)
    assert changed == []


def test_follow_up_date_completes_profile_and_generates_plan():
    partial = StudentMoveInProfile(
        school_name="Denison University",
        room_type=RoomType.double,
        budget_total=500.0,
    )
    orch = Orchestrator(settings=_settings(model_provider="mock"))
    state = orch.run_turn(
        session_id="follow-up",
        message="28th aug 2026",
        profile=partial,
    )

    assert state.route == "update_profile"
    assert state.profile.move_in_date is not None
    assert state.profile.move_in_date.month == 8
    assert state.profile.move_in_date.day == 28
    assert state.profile.move_in_date.year == 2026
    assert state.profile.is_minimally_complete
    assert state.plan is not None


def test_mock_provider_keeps_deterministic_demo_extraction():
    agent = ProfilePlannerAgent(settings=_settings(model_provider="mock"))
    message = (
        "I am moving into a double dorm at Denison on August 24. My total budget "
        "is $650. I already have pillows."
    )
    state = AgentState(session_id="demo", message=message, profile=StudentMoveInProfile())
    agent.run(state)

    assert state.profile.school_name == "Denison University"
    assert state.profile.room_type is RoomType.double
    assert state.profile.budget_total == 650.0
    assert state.profile.move_in_date is not None
