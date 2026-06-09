"""Focused agents coordinated by the orchestrator.

Planned agents:
- intake_agent: normalize and validate the student profile
- checklist_agent: build a personalized dorm checklist
- budget_agent: produce a budget-aware shopping plan
- recommendation_agent: category-level product recommendations
- timeline_agent: build the move-in timeline
- risk_agent: detect overspending, duplicates, prohibited items, gaps, late shipping

Each agent should accept the shared plan state and return an updated state so it
can run under either the mock orchestrator or a LangGraph graph.
"""
