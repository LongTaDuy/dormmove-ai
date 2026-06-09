"""Agent workflow orchestration.

This package defines a LangGraph-style orchestrator interface. A mock/rule-based
runner works first; a LangGraph-backed runner can be plugged in behind the same
interface without changing the API layer.
"""

# NOTE: keep this package __init__ lightweight. ``graph`` imports the agents,
# and the agents import ``orchestrator.state``; importing ``graph`` here would
# create a circular import. Import the orchestrator from ``app.orchestrator.graph``.
from app.orchestrator.state import AgentState

__all__ = ["AgentState"]
