"""In-memory telemetry for ModelRouter usage and estimated cost."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class _SessionUsage:
    calls: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class RuntimeLLMTelemetry:
    """Track per-session model usage for caps and observability."""

    _lock: Lock = field(default_factory=Lock)
    _session_usage: dict[str, _SessionUsage] = field(
        default_factory=lambda: defaultdict(_SessionUsage)
    )
    _failure_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _total_calls: int = 0

    def record(
        self,
        task_type: str,
        session_id: str | None,
        latency_seconds: float,
        fallback_used: bool,
        estimated_cost_usd: float,
    ) -> None:
        with self._lock:
            self._total_calls += 1
            if fallback_used:
                self._failure_counts[task_type] += 1
            if session_id:
                usage = self._session_usage[session_id]
                usage.calls += 1
                usage.estimated_cost_usd += estimated_cost_usd

    def session_usage(self, session_id: str) -> dict[str, float | int]:
        with self._lock:
            usage = self._session_usage.get(session_id, _SessionUsage())
            return {
                "calls": usage.calls,
                "estimatedCostUsd": round(usage.estimated_cost_usd, 6),
            }

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "totalCalls": self._total_calls,
                "failureCountsByTask": dict(self._failure_counts),
                "sessionCount": len(self._session_usage),
                "sessions": {
                    sid: {
                        "calls": u.calls,
                        "estimatedCostUsd": round(u.estimated_cost_usd, 6),
                    }
                    for sid, u in self._session_usage.items()
                },
            }
