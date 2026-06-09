"""API routes.

For now this exposes a versioned router with a meta endpoint. Plan, session,
and agent endpoints will be added on top of this in later steps.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__

router = APIRouter(prefix="/api/v1")


@router.get("/ping", tags=["meta"])
def ping() -> dict[str, str]:
    return {"message": "pong", "version": __version__}
