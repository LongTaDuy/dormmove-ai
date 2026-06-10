"""Keyword-based local retriever over curated dorm knowledge documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.rag.documents import LOCAL_DORM_KNOWLEDGE

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "is",
        "am",
        "are",
        "was",
        "be",
        "been",
        "being",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "it",
        "its",
        "this",
        "that",
        "with",
        "as",
        "by",
        "from",
        "so",
        "will",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "can",
        "just",
        "about",
        "into",
        "than",
        "then",
        "them",
        "they",
        "their",
        "there",
        "what",
        "when",
        "where",
        "which",
        "who",
        "how",
        "all",
        "any",
        "some",
        "very",
        "also",
        "already",
        "bring",
        "bringing",
    }
)

_TITLE_WEIGHT = 3.0
_TAG_WEIGHT = 2.5
_CONTENT_WEIGHT = 1.0


@dataclass(frozen=True)
class RetrievedDocument:
    doc_id: str
    title: str
    source_type: str
    content: str
    tags: list[str]
    risk_level: str
    score: float


class LocalKnowledgeRetriever:
    """Simple token-overlap retriever with optional tag filtering."""

    def __init__(self, documents: list[dict] | None = None) -> None:
        self._documents = documents or LOCAL_DORM_KNOWLEDGE

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        tags: list[str] | None = None,
    ) -> list[RetrievedDocument]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        filter_tags = {t.lower() for t in tags} if tags else None
        scored: list[RetrievedDocument] = []

        for doc in self._documents:
            doc_tags = {t.lower() for t in doc.get("tags", [])}
            if filter_tags and not doc_tags.intersection(filter_tags):
                continue

            score = self._score_document(query_tokens, doc)
            if filter_tags:
                overlap = len(query_tokens.intersection(doc_tags))
                score += overlap * _TAG_WEIGHT

            if score <= 0:
                continue

            scored.append(
                RetrievedDocument(
                    doc_id=doc["doc_id"],
                    title=doc["title"],
                    source_type=doc["source_type"],
                    content=doc["content"],
                    tags=list(doc.get("tags", [])),
                    risk_level=doc.get("risk_level", "low"),
                    score=round(score, 4),
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def _score_document(self, query_tokens: set[str], doc: dict) -> float:
        title_tokens = _tokenize(doc.get("title", ""))
        tag_tokens = _tokenize(" ".join(doc.get("tags", [])))
        content_tokens = _tokenize(doc.get("content", ""))

        score = 0.0
        score += len(query_tokens.intersection(title_tokens)) * _TITLE_WEIGHT
        score += len(query_tokens.intersection(tag_tokens)) * _TAG_WEIGHT
        score += len(query_tokens.intersection(content_tokens)) * _CONTENT_WEIGHT
        return score


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in _STOPWORDS and len(word) > 1}


_default_retriever = LocalKnowledgeRetriever()


def get_retriever() -> LocalKnowledgeRetriever:
    """Return the process-wide default knowledge retriever."""
    return _default_retriever
