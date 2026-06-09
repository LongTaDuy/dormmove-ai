"""Base class shared by all DormMove AI agents.

Agents are deterministic, rule-based units of work in this milestone. Each agent
takes the shared :class:`AgentState`, mutates it, records a trace entry, and
returns it. This keeps the contract identical to a LangGraph node, so the same
agents can later be wired into a graph without changes.
"""

from __future__ import annotations

from app.orchestrator.state import AgentState


class BaseAgent:
    """Common interface for all agents."""

    #: Human-readable agent name used in trace entries.
    name: str = "BaseAgent"

    def run(self, state: AgentState) -> AgentState:  # pragma: no cover - abstract
        raise NotImplementedError
