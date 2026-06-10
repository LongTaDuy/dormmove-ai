"""Local RAG-style knowledge retrieval for dorm move-in planning."""

from app.rag.documents import LOCAL_DORM_KNOWLEDGE
from app.rag.retriever import (
    LocalKnowledgeRetriever,
    RetrievedDocument,
    get_retriever,
)

__all__ = [
    "LOCAL_DORM_KNOWLEDGE",
    "LocalKnowledgeRetriever",
    "RetrievedDocument",
    "get_retriever",
]
