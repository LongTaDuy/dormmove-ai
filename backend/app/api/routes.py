"""API routes for DormMove AI.

Exposes a versioned router with session management and the chat endpoint that
drives the rule-based agent orchestrator. Session state is persisted via the
SQLite-backed :class:`SessionService` (resolved from ``app.state``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app import __version__
from app.memory import SessionService
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CreateSessionResponse,
    MoveInPlan,
    SessionSnapshotResponse,
    SessionSummary,
)
from app.orchestrator.graph import orchestrator

router = APIRouter(prefix="/api/v1")


def get_session_service(request: Request) -> SessionService:
    """Resolve the per-app SessionService set up during startup."""
    return request.app.state.session_service


@router.get("/ping", tags=["meta"])
def ping() -> dict[str, str]:
    return {"message": "pong", "version": __version__}


@router.post("/sessions", response_model=CreateSessionResponse, tags=["session"])
def create_session(
    service: SessionService = Depends(get_session_service),
) -> CreateSessionResponse:
    return service.create_session()


@router.get("/sessions", response_model=list[SessionSummary], tags=["session"])
def list_sessions(
    service: SessionService = Depends(get_session_service),
) -> list[SessionSummary]:
    return service.list_sessions()


@router.get(
    "/sessions/{session_id}",
    response_model=SessionSnapshotResponse,
    tags=["session"],
)
def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> SessionSnapshotResponse:
    if not service.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return service.get_session_snapshot(session_id)


@router.get(
    "/sessions/{session_id}/plan",
    response_model=MoveInPlan,
    tags=["session"],
)
def get_session_plan(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> MoveInPlan:
    if not service.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    plan = service.get_latest_plan(session_id)
    if plan is None:
        raise HTTPException(
            status_code=404,
            detail=f"No plan yet for session '{session_id}'. Send a chat message first.",
        )
    return plan


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(
    request: ChatRequest,
    service: SessionService = Depends(get_session_service),
) -> ChatResponse:
    if not service.session_exists(request.session_id):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Session '{request.session_id}' not found. "
                "Create one with POST /api/v1/sessions first."
            ),
        )

    # 1. Record the user's message.
    service.append_message(request.session_id, role="user", content=request.message)

    # 2. Load the saved profile and run the orchestrator with it.
    previous_profile = service.get_profile(request.session_id)
    state = orchestrator.run_turn(
        session_id=request.session_id,
        message=request.message,
        profile=previous_profile,
    )

    # 3. Persist the updated profile.
    service.save_profile(request.session_id, state.profile)

    # 4. Persist a plan snapshot when one was produced.
    if state.plan is not None:
        service.save_plan_snapshot(
            request.session_id, state.plan, state.plan.score_breakdown
        )

    # 5. Record the assistant reply with structured metadata.
    service.append_message(
        request.session_id,
        role="assistant",
        content=state.reply,
        meta={
            "trace": state.trace,
            "risk_flags": state.risk_flags,
            "missing_fields": state.missing_fields,
            "route": state.route,
        },
    )

    # 6. Return the structured response.
    return ChatResponse(
        session_id=request.session_id,
        reply=state.reply,
        profile=state.profile,
        plan=state.plan,
        missing_fields=state.missing_fields,
        risk_flags=state.risk_flags,
        trace=state.trace,
    )
