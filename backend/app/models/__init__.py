"""Pydantic domain models and API schemas.

This package is the contract shared across agents, scoring engine, API
responses, and the frontend. Import models from here, e.g.::

    from app.models import StudentMoveInProfile, MoveInPlan
"""

from app.models.schemas import (
    BudgetPreference,
    ChatRequest,
    ChatResponse,
    ChecklistItem,
    ChecklistStatus,
    CreateSessionResponse,
    DormItem,
    DormRuleRisk,
    ItemPriority,
    MoveInPlan,
    ProductCandidate,
    RoomType,
    ScoreBreakdown,
    SessionSnapshotResponse,
    SessionSummary,
    ShippingUrgency,
    StudentMoveInProfile,
    TimelineTask,
    TransportationMode,
    Verdict,
)

__all__ = [
    "BudgetPreference",
    "ChatRequest",
    "ChatResponse",
    "ChecklistItem",
    "ChecklistStatus",
    "CreateSessionResponse",
    "DormItem",
    "DormRuleRisk",
    "ItemPriority",
    "MoveInPlan",
    "ProductCandidate",
    "RoomType",
    "ScoreBreakdown",
    "SessionSnapshotResponse",
    "SessionSummary",
    "ShippingUrgency",
    "StudentMoveInProfile",
    "TimelineTask",
    "TransportationMode",
    "Verdict",
]
