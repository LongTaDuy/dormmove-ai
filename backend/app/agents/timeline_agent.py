"""MoveInTimelineAgent: build a move-in timeline and flag late shipping.

Generates phased tasks anchored on today's date and the student's move-in date.
Retrieved logistics knowledge grounds timeline advice in curated evidence.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.agents.base import BaseAgent
from app.models.schemas import TimelineTask, TransportationMode
from app.orchestrator.state import AgentState
from app.rag.retriever import LocalKnowledgeRetriever, RetrievedDocument, get_retriever


class MoveInTimelineAgent(BaseAgent):
    name = "MoveInTimelineAgent"

    def __init__(self, retriever: LocalKnowledgeRetriever | None = None) -> None:
        self._retriever = retriever or get_retriever()

    def run(self, state: AgentState) -> AgentState:
        profile = state.profile
        move_in = profile.move_in_date
        today = date.today()

        if move_in is None:
            state.add_trace(
                self.name,
                "skipped_timeline",
                "No move-in date set; timeline not generated.",
            )
            return state

        days_until = (move_in - today).days
        flying = profile.transportation_mode is TransportationMode.flight

        def due(days_before: int) -> date:
            target = move_in - timedelta(days=days_before)
            return max(target, today)

        tasks: list[TimelineTask] = [
            TimelineTask(
                task_id="confirm-rules",
                title="Confirm your dorm's official rules",
                phase="preparation",
                due_date=due(days_until),
                reason="Verify size/appliance limits before buying anything.",
            ),
            TimelineTask(
                task_id="coordinate-roommate",
                title="Coordinate shared items with your roommate",
                phase="preparation",
                due_date=due(max(days_until - 3, 0)),
                reason="Avoid duplicate fridges, rugs, and electronics.",
            ),
            TimelineTask(
                task_id="order-shipped",
                title="Order items that need shipping",
                phase="shopping",
                due_date=due(10),
                reason="Allow lead time so deliveries arrive before move-in.",
            ),
            TimelineTask(
                task_id="buy-essentials",
                title="Buy essential items",
                phase="shopping",
                due_date=due(7),
                reason="Lock in bedding, bath, and laundry basics early.",
            ),
            TimelineTask(
                task_id="pack-documents",
                title="Pack important documents",
                phase="packing",
                due_date=due(3),
                reason="Keep housing, ID, and insurance paperwork together.",
            ),
            TimelineTask(
                task_id="laundry-bath-prep",
                title="Prep laundry and bathroom kit",
                phase="packing",
                due_date=due(2),
                reason="Have towels, caddy, and detergent ready for day one.",
            ),
        ]

        if flying:
            tasks.append(
                TimelineTask(
                    task_id="pack-compact",
                    title="Pack compact, flight-friendly items",
                    phase="packing",
                    due_date=due(2),
                    reason="Flying limits luggage; prioritize small, light items.",
                )
            )
            if not any(t.task_id == "buy-bulky-after-arrival" for t in tasks):
                tasks.append(
                    TimelineTask(
                        task_id="buy-bulky-after-arrival",
                        title="Buy bulky items after you arrive",
                        phase="arrival",
                        due_date=move_in,
                        reason=(
                            "Purchase fridge, rugs, and storage locally to avoid "
                            "shipping."
                        ),
                    )
                )

        retrieval_query = " ".join(
            [
                state.message,
                profile.transportation_mode.value,
                "move-in timeline logistics shipping documents",
            ]
        )
        tags = ["logistics", "timeline", "move-in", "shipping"]
        if flying:
            tags.extend(["flight", "bulky", "compact"])
        retrieved = self._retriever.retrieve(retrieval_query, top_k=5, tags=tags)
        state.store_retrieved_context("timeline", _docs_to_dicts(retrieved))
        if retrieved:
            state.add_trace(
                self.name,
                "retrieved_timeline_context",
                f"Retrieved {len(retrieved)} logistics document(s).",
                evidence=_evidence_summary(retrieved),
            )
            doc_by_id = {doc.doc_id: doc for doc in retrieved}
            if "logistics-documents" in doc_by_id:
                doc = doc_by_id["logistics-documents"]
                for task in tasks:
                    if task.task_id == "pack-documents":
                        task.reason += f" [{doc.doc_id}] {doc.title}."
            if flying and "pack-buy-after-arrival" in doc_by_id:
                doc = doc_by_id["pack-buy-after-arrival"]
                for task in tasks:
                    if task.task_id == "buy-bulky-after-arrival":
                        task.reason += f" Evidence: [{doc.doc_id}] {doc.title}."

        flags: list[str] = []
        max_ship = max(
            (p.shipping_days for p in state.product_candidates), default=0
        )
        if days_until < 0:
            flags.append("Move-in date is in the past; update your date.")
        elif days_until <= max_ship:
            flags.append(
                f"Late shipping risk: only {days_until} day(s) until move-in but "
                f"some items take up to {max_ship} day(s) to ship. Buy in-store or expedite."
            )
        elif days_until < 10:
            flags.append(
                f"Tight timeline: {days_until} day(s) until move-in. Order shipped "
                "items immediately or buy locally."
            )

        if flags:
            for task in tasks:
                if task.task_id in {"order-shipped", "buy-bulky-after-arrival"}:
                    task.risk_flags.append("shipping timing")

        state.timeline = tasks
        state.add_risk_flags(flags)
        state.add_trace(
            self.name,
            "generated_timeline",
            (
                f"Generated {len(tasks)} timeline tasks; {days_until} day(s) "
                f"until move-in."
            ),
        )
        return state


def _docs_to_dicts(documents: list[RetrievedDocument]) -> list[dict]:
    return [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "source_type": doc.source_type,
            "content": doc.content,
            "tags": doc.tags,
            "risk_level": doc.risk_level,
            "score": doc.score,
        }
        for doc in documents
    ]


def _evidence_summary(documents: list[RetrievedDocument]) -> list[dict]:
    return [
        {"doc_id": doc.doc_id, "title": doc.title, "risk_level": doc.risk_level}
        for doc in documents
    ]
