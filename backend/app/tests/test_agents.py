"""Unit tests for individual DormMove AI agents."""

from datetime import date

from app.agents import (
    ChecklistAgent,
    ConciergeAgent,
    ProfilePlannerAgent,
    RulesAuditAgent,
)
from app.models.schemas import (
    BudgetPreference,
    ChecklistStatus,
    RoomType,
    StudentMoveInProfile,
    TransportationMode,
)
from app.orchestrator.state import AgentState

DEMO_MESSAGE = (
    "I am moving into a double dorm at Denison on August 24. My total budget "
    "is $650. I already have pillows, bedsheets, hangers, and a desk lamp. My "
    "roommate is bringing a mini fridge. I will fly to campus, so I prefer "
    "compact items and shipping to campus."
)


def _state(message: str, profile: StudentMoveInProfile | None = None) -> AgentState:
    return AgentState(
        session_id="test",
        message=message,
        profile=profile or StudentMoveInProfile(),
    )


def test_concierge_routes_planning_message_to_new_plan():
    state = _state(DEMO_MESSAGE)
    ConciergeAgent().run(state)
    assert state.route == "new_plan"


def test_profile_planner_extracts_all_demo_fields():
    state = _state(DEMO_MESSAGE)
    ProfilePlannerAgent().run(state)
    profile = state.profile

    assert profile.school_name == "Denison University"
    assert profile.room_type is RoomType.double
    assert profile.move_in_date is not None
    assert profile.move_in_date.month == 8
    assert profile.move_in_date.day == 24
    assert profile.budget_total == 650.0
    assert profile.transportation_mode is TransportationMode.flight

    owned_lower = [o.lower() for o in profile.already_owned_items]
    assert "pillows" in owned_lower
    assert "hangers" in owned_lower
    assert "desk lamp" in owned_lower

    roommate_lower = [r.lower() for r in profile.roommate_items]
    assert "mini fridge" in roommate_lower


def test_move_in_date_defaults_to_future_year():
    state = _state("Move-in is on August 24.")
    ProfilePlannerAgent().run(state)
    assert state.profile.move_in_date is not None
    assert state.profile.move_in_date >= date.today()


def test_profile_planner_does_not_overwrite_existing_school():
    profile = StudentMoveInProfile(school_name="Existing College")
    state = _state("Now at Denison", profile)
    ProfilePlannerAgent().run(state)
    assert state.profile.school_name == "Existing College"


def test_checklist_marks_already_owned_items():
    profile = StudentMoveInProfile(already_owned_items=["pillows", "hangers"])
    state = _state("checklist please", profile)
    ChecklistAgent().run(state)

    by_id = {c.item_id: c for c in state.checklist}
    assert by_id["pillows"].status is ChecklistStatus.already_owned
    assert by_id["hangers"].status is ChecklistStatus.already_owned


def test_checklist_marks_roommate_items():
    profile = StudentMoveInProfile(roommate_items=["mini fridge"])
    state = _state("checklist please", profile)
    ChecklistAgent().run(state)

    by_id = {c.item_id: c for c in state.checklist}
    assert by_id["mini-fridge"].status is ChecklistStatus.roommate_has


def test_checklist_flags_rule_risky_items_for_review():
    state = _state("checklist please")
    ChecklistAgent().run(state)
    by_id = {c.item_id: c for c in state.checklist}
    # The extension cord has check_rules risk in the seed catalog.
    assert by_id["surge-extension-cord"].status is ChecklistStatus.check_rules


def test_rules_audit_flags_generic_risky_items():
    profile = StudentMoveInProfile(
        already_owned_items=["scented candles", "a hot plate"]
    )
    state = _state("I also want to bring a space heater.", profile)
    RulesAuditAgent().run(state)

    assert state.risk_flags
    joined = " ".join(state.risk_flags).lower()
    assert "candle" in joined or "hot plate" in joined or "heater" in joined
    # Honesty: warnings are framed as generic.
    assert any("generic" in note.lower() for note in state.rule_notes)


def test_budget_preference_parsed_from_message():
    state = _state("I want the cheapest options possible.")
    ProfilePlannerAgent().run(state)
    assert state.profile.budget_preference is BudgetPreference.cheapest
