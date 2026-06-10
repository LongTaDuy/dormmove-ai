"""Tests for the local keyword-based knowledge retriever."""

from app.rag.documents import LOCAL_DORM_KNOWLEDGE
from app.rag.retriever import LocalKnowledgeRetriever


def test_retriever_returns_relevant_rule_docs():
    retriever = LocalKnowledgeRetriever()
    results = retriever.retrieve("candles hot plate extension cord", top_k=5)

    assert results
    titles = {doc.title.lower() for doc in results}
    assert any("candle" in title or "hot plate" in title or "extension" in title for title in titles)
    assert all(doc.score > 0 for doc in results)
    assert results == sorted(results, key=lambda d: d.score, reverse=True)


def test_retriever_returns_flight_packing_docs():
    retriever = LocalKnowledgeRetriever()
    results = retriever.retrieve("I am flying to campus", top_k=5)

    assert results
    doc_ids = {doc.doc_id for doc in results}
    assert "pack-compact-flight" in doc_ids or "pack-buy-after-arrival" in doc_ids


def test_tag_filtering_limits_results():
    retriever = LocalKnowledgeRetriever()
    all_results = retriever.retrieve("budget shopping", top_k=10)
    filtered = retriever.retrieve("budget shopping", top_k=10, tags=["budget"])

    assert filtered
    assert len(filtered) <= len(all_results)
    assert all("budget" in doc.tags for doc in filtered)


def test_knowledge_corpus_has_expected_size():
    assert 25 <= len(LOCAL_DORM_KNOWLEDGE) <= 40
