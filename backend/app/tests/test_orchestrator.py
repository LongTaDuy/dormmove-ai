"""Tests for the orchestrator pipeline and the /chat API endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import MoveInPlan, StudentMoveInProfile
from app.orchestrator.graph import orchestrator

client = TestClient(app)

DEMO_MESSAGE = (
    "I am moving into a double dorm at Denison on August 24. My total budget "
    "is $650. I already have pillows, bedsheets, hangers, and a desk lamp. My "
    "roommate is bringing a mini fridge. I will fly to campus, so I prefer "
    "compact items and shipping to campus."
)


def test_orchestrator_returns_move_in_plan_for_demo():
    state = orchestrator.run_turn(
        session_id="demo", message=DEMO_MESSAGE, profile=StudentMoveInProfile()
    )

    assert state.route == "new_plan"
    assert isinstance(state.plan, MoveInPlan)
    assert state.plan.checklist
    assert state.plan.timeline
    assert state.plan.score_breakdown.final_move_in_score >= 0.0
    # Trace contains a structured entry from each agent that ran.
    agents_in_trace = {entry["agent"] for entry in state.trace}
    assert "ConciergeAgent" in agents_in_trace
    assert "ChecklistAgent" in agents_in_trace
    assert "DecisionAgent" in agents_in_trace


def test_orchestrator_asks_for_missing_fields_when_incomplete():
    state = orchestrator.run_turn(
        session_id="incomplete",
        message="I'm a freshman and need help packing.",
        profile=StudentMoveInProfile(),
    )
    assert state.plan is None
    assert state.missing_fields
    assert "need" in state.reply.lower()


def test_chat_endpoint_returns_plan_and_trace():
    # Fresh session via the API.
    session_id = client.post("/api/v1/session").json()["session_id"]

    resp = client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": DEMO_MESSAGE},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["session_id"] == session_id
    assert body["plan"] is not None
    assert body["plan"]["checklist"]
    assert body["plan"]["score_breakdown"]["verdict"] in {
        "READY",
        "NEEDS_WORK",
        "HIGH_RISK",
    }
    assert "risk_flags" in body
    assert body["trace"]
    assert body["profile"]["school_name"] == "Denison University"


def test_chat_endpoint_persists_profile_across_turns():
    session_id = client.post("/api/v1/session").json()["session_id"]

    client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "I'm going to Denison."},
    )
    resp = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "It's a double room, move-in August 24, budget $700.",
        },
    )
    body = resp.json()
    # School from turn 1 persists into turn 2 and the plan now builds.
    assert body["profile"]["school_name"] == "Denison University"
    assert body["profile"]["room_type"] == "double"
    assert body["plan"] is not None
