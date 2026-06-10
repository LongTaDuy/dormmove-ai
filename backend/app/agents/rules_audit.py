"""RulesAuditAgent: flag risky or often-prohibited items.

Matches the user's message, stated items, restrictions, and the planned
checklist against the generic dorm-rule seed data. Retrieved local knowledge
grounds warnings in curated evidence snippets. All warnings remain explicitly
framed as *generic* because no school-specific rules are loaded.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.data.dorm_rules_seed import GENERIC_DORM_RULES
from app.models.schemas import DormRuleRisk
from app.orchestrator.state import AgentState
from app.rag.retriever import LocalKnowledgeRetriever, RetrievedDocument, get_retriever

GENERIC_DISCLAIMER = (
    "These are generic dorm-rule warnings; confirm against your school's "
    "official housing policy."
)


class RulesAuditAgent(BaseAgent):
    name = "RulesAuditAgent"

    def __init__(self, retriever: LocalKnowledgeRetriever | None = None) -> None:
        self._retriever = retriever or get_retriever()

    def run(self, state: AgentState) -> AgentState:
        profile = state.profile
        haystack_parts: list[str] = [state.message.lower()]
        haystack_parts += [s.lower() for s in profile.already_owned_items]
        haystack_parts += [s.lower() for s in profile.roommate_items]
        haystack_parts += [s.lower() for s in profile.restrictions]
        haystack_parts += [s.lower() for s in profile.preferences]
        haystack_parts += [c.name.lower() for c in state.checklist]
        haystack = " | ".join(haystack_parts)

        risky_items = [
            c.name
            for c in state.checklist
            if c.status.value in {"check_rules", "needed"}
            and c.risk_flags
        ]
        retrieval_query = " ".join(
            [
                state.message,
                " ".join(profile.restrictions),
                " ".join(risky_items),
                haystack,
            ]
        )
        retrieved = self._retriever.retrieve(
            retrieval_query,
            top_k=5,
            tags=["rules", "prohibited", "safety", "electrical", "appliances"],
        )
        state.store_retrieved_context("rules", _docs_to_dicts(retrieved))
        if retrieved:
            state.add_trace(
                self.name,
                "retrieved_rule_context",
                f"Retrieved {len(retrieved)} generic rule document(s).",
                evidence=_evidence_summary(retrieved),
            )

        flags: list[str] = []
        notes: list[str] = []
        for rule in GENERIC_DORM_RULES:
            keywords = rule.get("keywords", [])
            if any(kw.lower() in haystack for kw in keywords):
                risk = rule.get("risk", DormRuleRisk.check_rules.value)
                title = rule.get("title", rule.get("rule_id", "rule"))
                warning = rule.get("warning", "")
                if risk == DormRuleRisk.often_prohibited.value:
                    flags.append(f"Often prohibited: {title}")
                elif risk == DormRuleRisk.check_rules.value:
                    flags.append(f"Check dorm rules: {title}")
                notes.append(f"{title}: {warning}")

        for doc in retrieved:
            if doc.risk_level in {"medium", "high"}:
                cite = f"[{doc.doc_id}] {doc.title}"
                note = f"Knowledge: {cite} — {doc.content}"
                if note not in notes:
                    notes.append(note)

        for item in state.checklist:
            if item.status.value == "check_rules":
                flag = f"Check dorm rules: {item.name}"
                if flag not in flags:
                    flags.append(flag)

        if flags and GENERIC_DISCLAIMER not in notes:
            notes.append(GENERIC_DISCLAIMER)

        state.add_risk_flags(flags)
        for note in notes:
            if note not in state.rule_notes:
                state.rule_notes.append(note)

        summary = (
            f"Flagged {len(flags)} potential rule risk(s)."
            if flags
            else "No generic dorm-rule risks detected."
        )
        if retrieved:
            cited = ", ".join(doc.doc_id for doc in retrieved[:3])
            summary += f" Evidence: {cited}."
        state.add_trace(self.name, "audited_rules", summary)
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
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "risk_level": doc.risk_level,
        }
        for doc in documents
    ]
