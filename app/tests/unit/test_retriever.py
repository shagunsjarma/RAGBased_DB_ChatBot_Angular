"""Unit tests for the RAG retriever module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.retriever import RetrievalResult, SchemaRetriever


@pytest.mark.asyncio
async def test_retriever_retrieve_format() -> None:
    # Mock dependencies
    embedder_mock = AsyncMock()
    embedder_mock.generate_query_embedding.return_value = [0.1, 0.2, 0.3]

    store_mock = AsyncMock()
    store_mock.search.return_value = [
        {"text": "Table structure users", "score": 0.9, "table_name": "users", "chunk_type": "table_def"},
        {"text": "Table structure orders", "score": 0.8, "table_name": "orders", "chunk_type": "table_def"},
    ]

    retriever = SchemaRetriever(embedding_generator=embedder_mock, vector_store=store_mock)

    # Execute
    results = await retriever.retrieve("Show users and orders", top_k=5)

    # Verify
    assert len(results) == 2
    assert results[0].table_name == "users"
    assert results[0].score == 0.9
    assert results[1].table_name == "orders"
    assert results[1].score == 0.8

    embedder_mock.generate_query_embedding.assert_awaited_once_with("Show users and orders")
    store_mock.search.assert_awaited_once_with([0.1, 0.2, 0.3], limit=5, table_filter=None)


def test_retriever_format_context() -> None:
    retriever = SchemaRetriever(embedding_generator=None, vector_store=None)
    results = [
        RetrievalResult(text="Table users definition", score=0.9, table_name="users", chunk_type="table_def"),
        RetrievalResult(text="Table orders definition", score=0.8, table_name="orders", chunk_type="table_def"),
    ]

    context = retriever.format_context(results)
    
    assert "DATABASE SCHEMA CONTEXT:" in context
    assert "Table users definition" in context
    assert "Table orders definition" in context
