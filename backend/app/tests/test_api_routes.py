"""Tests for the polished FastAPI route surface."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DEMO_MESSAGE = (
    "I am moving into a double dorm at Denison on August 24. My total budget "
    "is $650. I already have pillows, bedsheets, hangers, and a desk lamp. My "
    "roommate is bringing a mini fridge. I will fly to campus, so I prefer "
    "compact items and shipping to campus."
)


def _create_session(title: str | None = None) -> str:
    if title is None:
        resp = client.post("/api/v1/sessions")
    else:
        resp = client.post("/api/v1/sessions", json={"title": title})
    assert resp.status_code == 200
    return resp.json()["session_id"]


def _chat(session_id: str, message: str = DEMO_MESSAGE) -> dict:
    resp = client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": message},
    )
    assert resp.status_code == 200
    return resp.json()


def test_post_sessions_works_with_no_body():
    sid = _create_session()
    assert sid


def test_post_sessions_works_with_custom_title():
    sid = _create_session(title="My Denison Move-In Plan")
    listing = client.get("/api/v1/sessions").json()
    match = next(s for s in listing if s["session_id"] == sid)
    assert match["title"] == "My Denison Move-In Plan"


def test_list_sessions_includes_summary_fields():
    sid = _create_session()
    _chat(sid)

    listing = client.get("/api/v1/sessions")
    assert listing.status_code == 200
    match = next(s for s in listing.json() if s["session_id"] == sid)
    assert match["message_count"] >= 2
    assert match["has_plan"] is True
    assert match["latest_score"] is not None
    assert match["latest_verdict"] in {"READY", "NEEDS_WORK", "HIGH_RISK"}


def test_get_session_returns_snapshot():
    sid = _create_session()
    _chat(sid)

    resp = client.get(f"/api/v1/sessions/{sid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == sid
    assert body["profile"]["school_name"] == "Denison University"
    assert len(body["messages"]) >= 2
    assert body["latest_plan"] is not None
    assert body["latest_score"] is not None


def test_get_plan_404_before_chat():
    sid = _create_session()
    resp = client.get(f"/api/v1/sessions/{sid}/plan")
    assert resp.status_code == 404
    assert "No plan has been generated" in resp.json()["detail"]


def test_chat_generates_and_persists_plan():
    sid = _create_session()
    body = _chat(sid)
    assert body["plan"] is not None
    assert body["plan"]["checklist"]
    assert body["plan"]["product_candidates"]
    assert body["plan"]["timeline"]
    assert body["plan"]["score_breakdown"]
    assert "missing_fields" in body
    assert "risk_flags" in body
    assert body["trace"]


def test_get_plan_after_chat():
    sid = _create_session()
    _chat(sid)

    resp = client.get(f"/api/v1/sessions/{sid}/plan")
    assert resp.status_code == 200
    assert resp.json()["checklist"]


def test_get_checklist_returns_summary():
    sid = _create_session()
    _chat(sid)

    resp = client.get(f"/api/v1/sessions/{sid}/checklist")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == sid
    assert body["checklist"]
    summary = body["summary"]
    assert summary["total"] == len(body["checklist"])
    assert summary["needed"] + summary["already_owned"] + summary["roommate_has"] + summary["check_rules"] <= summary["total"]
    assert summary["estimated_remaining_cost"] >= 0


def test_get_products_returns_grouped_categories():
    sid = _create_session()
    _chat(sid)

    resp = client.get(f"/api/v1/sessions/{sid}/products")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == sid
    assert isinstance(body["categories"], dict)
    assert body["categories"]
    summary = body["summary"]
    assert summary["total_products"] > 0
    assert summary["category_count"] == len(body["categories"])
    assert summary["avg_price"] > 0
    assert summary["avg_rating"] > 0


def test_get_timeline_returns_summary():
    sid = _create_session()
    _chat(sid)

    resp = client.get(f"/api/v1/sessions/{sid}/timeline")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == sid
    assert body["timeline"]
    summary = body["summary"]
    assert summary["total_tasks"] == len(body["timeline"])
    assert summary["phases"]
    assert summary["risk_flag_count"] >= 0


def test_runtime_metrics_after_chat():
    sid = _create_session()
    _chat(sid)

    resp = client.get("/api/v1/metrics/runtime")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_count"] >= 1
    assert body["message_count"] >= 2
    assert body["plan_snapshot_count"] >= 1
    assert body["average_final_move_in_score"] is not None
    assert body["verdict_counts"]
    assert "generated_at" in body


def test_invalid_session_returns_404():
    bad = "invalid-session-id"
    endpoints = [
        ("GET", f"/api/v1/sessions/{bad}/plan"),
        ("GET", f"/api/v1/sessions/{bad}/checklist"),
        ("GET", f"/api/v1/sessions/{bad}/products"),
        ("GET", f"/api/v1/sessions/{bad}/timeline"),
    ]
    for method, path in endpoints:
        resp = client.request(method, path)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Session not found."

    chat_resp = client.post(
        "/api/v1/chat",
        json={"session_id": bad, "message": "hello"},
    )
    assert chat_resp.status_code == 404
    assert chat_resp.json()["detail"] == "Session not found."
