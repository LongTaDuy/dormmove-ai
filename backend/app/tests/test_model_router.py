"""Tests for ModelRouter mock mode, caps, and fallback behavior."""

from __future__ import annotations

import asyncio

import pytest

from app.core.config import Settings
from app.core.model_router import ModelRouter


def _settings(**kwargs) -> Settings:
    """Build settings isolated from local .env files."""
    return Settings(_env_file=None, **kwargs)


def _run(coro):
    return asyncio.run(coro)


def test_mock_mode_returns_output_without_api_key():
    router = ModelRouter(_settings(model_provider="mock", openai_api_key=None))
    result = _run(
        router.call(
            task_type="profile_extraction",
            payload={"message": "Double room at Denison, budget $500"},
            session_id="mock-session",
        )
    )
    assert result.model_id == "mock"
    assert result.fallback_used is False
    assert "confidence" in result.output


def test_mock_mode_enforces_max_model_calls_per_session():
    settings = _settings(
        model_provider="mock",
        max_model_calls_per_session=2,
        estimated_cost_per_call_usd=0.001,
    )
    router = ModelRouter(settings)
    session_id = "capped-session"

    _run(router.call("intent_classification", {"message": "hi"}, session_id))
    _run(router.call("intent_classification", {"message": "hello"}, session_id))

    with pytest.raises(RuntimeError, match="max model calls"):
        _run(router.call("intent_classification", {"message": "again"}, session_id))


async def _failing_invoke(_task_type: str, _payload: dict) -> dict:
    raise RuntimeError("injected provider failure")


def test_fallback_returns_fallback_used_when_invoke_fn_fails():
    settings = _settings(
        model_provider="openai",
        openai_api_key="test-key-not-used",
        allow_llm_fallback=True,
        llm_max_retries=0,
    )
    router = ModelRouter(settings, invoke_fn=_failing_invoke)
    result = _run(
        router.call(
            task_type="intent_classification",
            payload={"message": "checklist please"},
            session_id="fallback-session",
        )
    )
    assert result.fallback_used is True
    assert result.fallback_reason is not None
    assert result.output.get("intent") == "ask_checklist"


def test_snapshot_metrics_tracks_session_usage():
    settings = _settings(model_provider="mock")
    router = ModelRouter(settings)
    _run(
        router.call(
            "profile_extraction",
            {"message": "Denison"},
            session_id="metrics-session",
        )
    )
    usage = router.telemetry.session_usage("metrics-session")
    assert usage["calls"] == 1
    assert usage["estimatedCostUsd"] > 0
    metrics = router.snapshot_metrics()
    assert metrics["provider"] == "mock"
    assert metrics["totalCalls"] >= 1
