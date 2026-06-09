"""MoveInTimelineAgent: build a move-in timeline and flag late shipping.

Generates phased tasks anchored on today's date and the student's move-in date.
Tasks adapt to transportation mode (e.g. flying favors compact shipping and
buying bulky items after arrival).
"""

from __future__ import annotations

from datetime import date, timedelta

from app.agents.base import BaseAgent
from app.models.schemas import TimelineTask, TransportationMode
from app.orchestrator.state import AgentState


class MoveInTimelineAgent(BaseAgent):
    name = "MoveInTimelineAgent"

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
                due_date=due(days_until),  # as soon as possible
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
            tasks.append(
                TimelineTask(
                    task_id="buy-bulky-after-arrival",
                    title="Buy bulky items after you arrive",
                    phase="arrival",
                    due_date=move_in,
                    reason="Purchase fridge, rugs, and storage locally to avoid shipping.",
                )
            )

        # Late-shipping risk: not enough lead time for shipped products.
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
