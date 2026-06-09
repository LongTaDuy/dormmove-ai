"""API routes for DormMove AI.

Frontend-ready session management, plan views, runtime metrics, and the chat
endpoint. Session state is persisted via the SQLite-backed
:class:`SessionService` (resolved from ``app.state``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app import __version__
from app.memory import SessionService
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChecklistEnvelopeResponse,
    ChecklistStatus,
    ChecklistSummary,
    CreateSessionRequest,
    CreateSessionResponse,
    MoveInPlan,
    ProductRecommendationsEnvelopeResponse,
    ProductRecommendationsSummary,
    RuntimeMetricsResponse,
    SessionSnapshotResponse,
    SessionSummary,
    TimelineEnvelopeResponse,
    TimelineSummary,
)
from app.orchestrator.graph import orchestrator

router = APIRouter(prefix="/api/v1")

_SESSION_NOT_FOUND = "Session not found."
_NO_PLAN = "No plan has been generated for this session yet."


def get_session_service(request: Request) -> SessionService:
    """Resolve the per-app SessionService set up during startup."""
    return request.app.state.session_service


def _require_session(service: SessionService, session_id: str) -> None:
    if not service.session_exists(session_id):
        raise HTTPException(status_code=404, detail=_SESSION_NOT_FOUND)


def _require_plan(service: SessionService, session_id: str) -> MoveInPlan:
    _require_session(service, session_id)
    plan = service.get_latest_plan(session_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=_NO_PLAN)
    return plan


def _build_checklist_envelope(
    session_id: str, plan: MoveInPlan
) -> ChecklistEnvelopeResponse:
    checklist = plan.checklist
    spending_statuses = {ChecklistStatus.needed, ChecklistStatus.check_rules}
    summary = ChecklistSummary(
        total=len(checklist),
        needed=sum(1 for c in checklist if c.status is ChecklistStatus.needed),
        already_owned=sum(
            1 for c in checklist if c.status is ChecklistStatus.already_owned
        ),
        roommate_has=sum(
            1 for c in checklist if c.status is ChecklistStatus.roommate_has
        ),
        check_rules=sum(
            1 for c in checklist if c.status is ChecklistStatus.check_rules
        ),
        estimated_remaining_cost=round(
            sum(c.estimated_price for c in checklist if c.status in spending_statuses),
            2,
        ),
    )
    return ChecklistEnvelopeResponse(
        session_id=session_id, checklist=checklist, summary=summary
    )


def _build_products_envelope(
    session_id: str, plan: MoveInPlan
) -> ProductRecommendationsEnvelopeResponse:
    categories: dict[str, list] = {}
    for product in plan.product_candidates:
        categories.setdefault(product.category, []).append(product)

    products = plan.product_candidates
    if products:
        avg_price = round(sum(p.price for p in products) / len(products), 2)
        avg_rating = round(sum(p.rating for p in products) / len(products), 2)
    else:
        avg_price = 0.0
        avg_rating = 0.0

    summary = ProductRecommendationsSummary(
        total_products=len(products),
        category_count=len(categories),
        avg_price=avg_price,
        avg_rating=avg_rating,
    )
    return ProductRecommendationsEnvelopeResponse(
        session_id=session_id, categories=categories, summary=summary
    )


def _build_timeline_envelope(
    session_id: str, plan: MoveInPlan
) -> TimelineEnvelopeResponse:
    timeline = plan.timeline
    phases = list(dict.fromkeys(task.phase for task in timeline))
    risk_flag_count = sum(len(task.risk_flags) for task in timeline)
    summary = TimelineSummary(
        total_tasks=len(timeline),
        phases=phases,
        risk_flag_count=risk_flag_count,
    )
    return TimelineEnvelopeResponse(
        session_id=session_id, timeline=timeline, summary=summary
    )


@router.get("/ping", tags=["meta"])
def ping() -> dict[str, str]:
    return {"message": "pong", "version": __version__}


@router.post("/sessions", response_model=CreateSessionResponse, tags=["session"])
def create_session(
    body: CreateSessionRequest | None = None,
    service: SessionService = Depends(get_session_service),
) -> CreateSessionResponse:
    title = body.title if body else None
    return service.create_session(title=title)


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
    _require_session(service, session_id)
    return service.get_session_snapshot(session_id)


@router.get(
    "/sessions/{session_id}/plan",
    response_model=MoveInPlan,
    tags=["session", "plan"],
)
def get_session_plan(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> MoveInPlan:
    return _require_plan(service, session_id)


@router.get(
    "/sessions/{session_id}/checklist",
    response_model=ChecklistEnvelopeResponse,
    tags=["session", "plan"],
)
def get_session_checklist(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> ChecklistEnvelopeResponse:
    plan = _require_plan(service, session_id)
    return _build_checklist_envelope(session_id, plan)


@router.get(
    "/sessions/{session_id}/products",
    response_model=ProductRecommendationsEnvelopeResponse,
    tags=["session", "plan"],
)
def get_session_products(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> ProductRecommendationsEnvelopeResponse:
    plan = _require_plan(service, session_id)
    return _build_products_envelope(session_id, plan)


@router.get(
    "/sessions/{session_id}/timeline",
    response_model=TimelineEnvelopeResponse,
    tags=["session", "plan"],
)
def get_session_timeline(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> TimelineEnvelopeResponse:
    plan = _require_plan(service, session_id)
    return _build_timeline_envelope(session_id, plan)


@router.get(
    "/metrics/runtime",
    response_model=RuntimeMetricsResponse,
    tags=["metrics"],
)
def get_runtime_metrics(
    service: SessionService = Depends(get_session_service),
) -> RuntimeMetricsResponse:
    return service.get_runtime_metrics()


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(
    request: ChatRequest,
    service: SessionService = Depends(get_session_service),
) -> ChatResponse:
    _require_session(service, request.session_id)

    service.append_message(request.session_id, role="user", content=request.message)

    previous_profile = service.get_profile(request.session_id)
    state = orchestrator.run_turn(
        session_id=request.session_id,
        message=request.message,
        profile=previous_profile,
    )

    service.save_profile(request.session_id, state.profile)

    if state.plan is not None:
        service.save_plan_snapshot(
            request.session_id, state.plan, state.plan.score_breakdown
        )

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

    return ChatResponse(
        session_id=request.session_id,
        reply=state.reply,
        profile=state.profile,
        plan=state.plan,
        missing_fields=state.missing_fields,
        risk_flags=state.risk_flags,
        trace=state.trace,
    )
