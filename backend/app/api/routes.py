"""API routes for DormMove AI.

Exposes a versioned router with the chat endpoint that drives the rule-based
agent orchestrator.

NOTE (temporary): session state is kept in a process-local in-memory dict.
This is intentionally simple for this milestone and will be replaced by the
SQLite-backed session store (and optional Redis checkpointing) in a later step.
Do not rely on this for multi-process or persistent deployments.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from fastapi import APIRouter

from app import __version__
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CreateSessionResponse,
    MoveInPlan,
    StudentMoveInProfile,
)
from app.orchestrator.graph import orchestrator

router = APIRouter(prefix="/api/v1")


@dataclass
class _SessionState:
    """TODO: replace with persistent SQLite-backed session storage."""

    profile: StudentMoveInProfile = field(default_factory=StudentMoveInProfile)
    plan: MoveInPlan | None = None
    message_count: int = 0


# TODO: temporary in-memory session store (not persistent, not multi-process safe).
_SESSIONS: dict[str, _SessionState] = {}


@router.get("/ping", tags=["meta"])
def ping() -> dict[str, str]:
    return {"message": "pong", "version": __version__}


@router.post("/session", response_model=CreateSessionResponse, tags=["session"])
def create_session() -> CreateSessionResponse:
    session_id = uuid.uuid4().hex
    _SESSIONS[session_id] = _SessionState()
    return CreateSessionResponse(session_id=session_id)


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest) -> ChatResponse:
    # 1. Load previous session state (create lazily if unknown).
    session = _SESSIONS.setdefault(request.session_id, _SessionState())

    # 2. Run the orchestrator with the prior profile.
    state = orchestrator.run_turn(
        session_id=request.session_id,
        message=request.message,
        profile=session.profile,
    )

    # 3. Update in-memory session state (TODO: persist instead).
    session.profile = state.profile
    if state.plan is not None:
        session.plan = state.plan
    session.message_count += 1

    # 4. Return the structured response.
    return ChatResponse(
        session_id=request.session_id,
        reply=state.reply,
        profile=state.profile,
        plan=state.plan,
        missing_fields=state.missing_fields,
        risk_flags=state.risk_flags,
        trace=state.trace,
    )
