"""Tests for SQLite-backed session memory and the session/chat API."""

import time
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.memory.session_service import SessionService
from app.models.schemas import (
    MoveInPlan,
    RoomType,
    ScoreBreakdown,
    StudentMoveInProfile,
    Verdict,
)

client = TestClient(app)

DEMO_MESSAGE = (
    "I am moving into a double dorm at Denison on August 24. My total budget "
    "is $650. I already have pillows, bedsheets, hangers, and a desk lamp. My "
    "roommate is bringing a mini fridge. I will fly to campus, so I prefer "
    "compact items and shipping to campus."
)


@pytest.fixture()
def service(tmp_path) -> SessionService:
    svc = SessionService(str(tmp_path / "sessions.sqlite3"))
    svc.initialize()
    return svc


def _sample_plan() -> tuple[MoveInPlan, ScoreBreakdown]:
    score = ScoreBreakdown(final_move_in_score=0.8, verdict=Verdict.READY)
    plan = MoveInPlan(
        profile=StudentMoveInProfile(school_name="Denison University"),
        score_breakdown=score,
        final_summary="Looks good.",
    )
    return plan, score


# -- unit tests --------------------------------------------------------------


def test_initialize_creates_tables(service: SessionService):
    tables = service.store.query_all(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    names = {row["name"] for row in tables}
    assert {"sessions", "messages", "plan_snapshots"} <= names


def test_create_session_and_exists(service: SessionService):
    created = service.create_session()
    assert created.session_id
    assert service.session_exists(created.session_id)
    assert not service.session_exists("does-not-exist")


def test_save_and_get_profile_roundtrip(service: SessionService):
    sid = service.create_session().session_id
    profile = StudentMoveInProfile(
        school_name="Denison University",
        room_type=RoomType.double,
        move_in_date=date(2026, 8, 24),
        budget_total=650.0,
        already_owned_items=["pillows", "hangers"],
    )
    service.save_profile(sid, profile)

    loaded = service.get_profile(sid)
    assert loaded.school_name == "Denison University"
    assert loaded.room_type is RoomType.double
    assert loaded.move_in_date == date(2026, 8, 24)
    assert loaded.budget_total == 650.0
    assert loaded.already_owned_items == ["pillows", "hangers"]


def test_get_profile_defaults_when_empty(service: SessionService):
    sid = service.create_session().session_id
    loaded = service.get_profile(sid)
    assert isinstance(loaded, StudentMoveInProfile)
    assert loaded.school_name is None


def test_append_message_then_get_history_in_order(service: SessionService):
    sid = service.create_session().session_id
    service.append_message(sid, "user", "first")
    service.append_message(sid, "assistant", "second", meta={"route": "new_plan"})
    service.append_message(sid, "user", "third")

    history = service.get_history(sid)
    assert [m["content"] for m in history] == ["first", "second", "third"]
    assert [m["role"] for m in history] == ["user", "assistant", "user"]
    assert history[1]["meta"]["route"] == "new_plan"


def test_save_plan_snapshot_stores_latest(service: SessionService):
    sid = service.create_session().session_id
    plan, score = _sample_plan()
    service.save_plan_snapshot(sid, plan, score)

    latest = service.get_latest_plan(sid)
    assert latest is not None
    assert latest.score_breakdown.verdict is Verdict.READY

    snapshot = service.get_session_snapshot(sid)
    assert snapshot.latest_plan is not None
    assert snapshot.latest_score is not None
    assert snapshot.latest_score.final_move_in_score == 0.8


def test_list_sessions_sorted_by_updated_at_desc(service: SessionService):
    first = service.create_session().session_id
    time.sleep(0.01)
    second = service.create_session().session_id
    time.sleep(0.01)
    # Touch the first session so it becomes the most recently updated.
    service.append_message(first, "user", "hello")

    sessions = service.list_sessions()
    ids = [s.session_id for s in sessions]
    assert ids[0] == first
    assert second in ids


def test_get_session_snapshot_includes_everything(service: SessionService):
    sid = service.create_session().session_id
    service.save_profile(
        sid, StudentMoveInProfile(school_name="Denison University")
    )
    service.append_message(sid, "user", "hi")
    plan, score = _sample_plan()
    service.save_plan_snapshot(sid, plan, score)

    snapshot = service.get_session_snapshot(sid)
    assert snapshot.session_id == sid
    assert snapshot.title
    assert snapshot.created_at
    assert snapshot.profile.school_name == "Denison University"
    assert len(snapshot.messages) == 1
    assert snapshot.latest_plan is not None
    assert snapshot.latest_score is not None


def test_get_history_unknown_session_is_empty(service: SessionService):
    assert service.get_history("nope") == []


# -- API tests ---------------------------------------------------------------


def test_post_sessions_creates_session():
    resp = client.post("/api/v1/sessions")
    assert resp.status_code == 200
    sid = resp.json()["session_id"]
    assert sid

    # The new session shows up in the listing.
    listing = client.get("/api/v1/sessions")
    assert listing.status_code == 200
    assert any(s["session_id"] == sid for s in listing.json())


def test_chat_with_invalid_session_returns_404():
    resp = client.post(
        "/api/v1/chat",
        json={"session_id": "unknown-session-id", "message": "hello"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_chat_persists_messages_profile_and_plan():
    sid = client.post("/api/v1/sessions").json()["session_id"]

    resp = client.post(
        "/api/v1/chat",
        json={"session_id": sid, "message": DEMO_MESSAGE},
    )
    assert resp.status_code == 200
    assert resp.json()["plan"] is not None

    # Snapshot reflects the persisted user + assistant messages and the plan.
    snapshot = client.get(f"/api/v1/sessions/{sid}").json()
    roles = [m["role"] for m in snapshot["messages"]]
    assert "user" in roles and "assistant" in roles
    assert snapshot["profile"]["school_name"] == "Denison University"
    assert snapshot["latest_plan"] is not None

    # The latest-plan endpoint returns the stored plan.
    plan_resp = client.get(f"/api/v1/sessions/{sid}/plan")
    assert plan_resp.status_code == 200
    assert plan_resp.json()["checklist"]


def test_get_plan_404_before_any_chat():
    sid = client.post("/api/v1/sessions").json()["session_id"]
    resp = client.get(f"/api/v1/sessions/{sid}/plan")
    assert resp.status_code == 404
