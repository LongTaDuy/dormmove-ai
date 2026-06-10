"""Tests for RAG integration in planning agents and orchestrator trace."""

from fastapi.testclient import TestClient

from app.agents import MoveInTimelineAgent, RulesAuditAgent
from app.agents.checklist_agent import ChecklistAgent
from app.main import app
from app.models.schemas import (
    RoomType,
    StudentMoveInProfile,
    TransportationMode,
)
from app.orchestrator.graph import orchestrator
from app.orchestrator.state import AgentState

client = TestClient(app)

DEMO_MESSAGE = (
    "I am moving into a double dorm at Denison on August 24. My total budget "
    "is $650. I already have pillows, bedsheets, hangers, and a desk lamp. My "
    "roommate is bringing a mini fridge. I will fly to campus, so I prefer "
    "compact items and shipping to campus."
)


def _state(
    message: str,
    profile: StudentMoveInProfile | None = None,
) -> AgentState:
    return AgentState(
        session_id="rag-test",
        message=message,
        profile=profile or StudentMoveInProfile(),
    )


def test_rules_audit_agent_stores_retrieved_rule_context():
    profile = StudentMoveInProfile(
        restrictions=["no candles"],
        already_owned_items=["extension cord"],
    )
    state = _state("I have a hot plate and candles", profile)
    ChecklistAgent().run(state)
    RulesAuditAgent().run(state)

    assert "rules" in state.retrieved_context
    assert state.retrieved_context["rules"]
    retrieval_trace = [
        entry
        for entry in state.trace
        if entry.get("action") == "retrieved_rule_context"
    ]
    assert retrieval_trace
    assert retrieval_trace[0].get("evidence")


def test_timeline_agent_stores_retrieved_logistics_context():
    profile = StudentMoveInProfile(
        move_in_date=__import__("datetime").date(2026, 8, 24),
        transportation_mode=TransportationMode.flight,
        room_type=RoomType.double,
    )
    state = _state(DEMO_MESSAGE, profile)
    ChecklistAgent().run(state)
    MoveInTimelineAgent().run(state)

    assert "timeline" in state.retrieved_context
    assert state.retrieved_context["timeline"]
    retrieval_trace = [
        entry
        for entry in state.trace
        if entry.get("action") == "retrieved_timeline_context"
    ]
    assert retrieval_trace
    assert retrieval_trace[0].get("evidence")
    assert any(
        task.task_id == "buy-bulky-after-arrival" for task in state.timeline
    )


def test_orchestrator_trace_includes_retrieved_evidence():
    state = orchestrator.run_turn(
        session_id="rag-demo",
        message=DEMO_MESSAGE,
        profile=StudentMoveInProfile(),
    )

    assert state.plan is not None
    evidence_entries = [
        entry for entry in state.trace if entry.get("evidence")
    ]
    assert evidence_entries
    agents_with_evidence = {entry["agent"] for entry in evidence_entries}
    assert "RulesAuditAgent" in agents_with_evidence
    assert "ChecklistAgent" in agents_with_evidence or "MoveInTimelineAgent" in agents_with_evidence


def test_knowledge_search_endpoint_returns_results():
    resp = client.get(
        "/api/v1/knowledge/search",
        params={"q": "candles hot plate", "top_k": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body
    assert "doc_id" in body[0]
    assert body[0]["score"] > 0
