"""Schema retriever – queries vector store for relevant schema context."""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.vector_store import VectorStore


@dataclass
class RetrievalResult:
    text: str
    score: float
    table_name: str
    chunk_type: str


class SchemaRetriever:
    """Retrieves relevant schema context from the vector store."""

    def __init__(self, embedding_generator: EmbeddingGenerator, vector_store: VectorStore) -> None:
        self._embedder = embedding_generator
        self._store = vector_store

    async def retrieve(self, query: str, top_k: int = 10, table_filter: str | None = None) -> list[RetrievalResult]:
        """Embed query and search vector store."""
        query_embedding = await self._embedder.generate_query_embedding(query)
        results = await self._store.search(query_embedding, limit=top_k, table_filter=table_filter)
        return [
            RetrievalResult(text=r["text"], score=r["score"], table_name=r["table_name"], chunk_type=r["chunk_type"])
            for r in results
        ]

    async def retrieve_for_tables(self, table_names: list[str], top_k_per_table: int = 3) -> list[RetrievalResult]:
        """Retrieve schema info for specific tables."""
        all_results: list[RetrievalResult] = []
        for table in table_names:
            results = await self.retrieve(f"schema for table {table}", top_k=top_k_per_table, table_filter=table)
            all_results.extend(results)
        return all_results

    def format_context(self, results: list[RetrievalResult]) -> str:
        """Format retrieval results into a context string for LLM."""
        if not results:
            return "No schema context available."

        seen = set()
        lines = ["DATABASE SCHEMA CONTEXT:", "=" * 40]
        for r in sorted(results, key=lambda x: x.score, reverse=True):
            key = (r.table_name, r.chunk_type)
            if key in seen:
                continue
            seen.add(key)
            lines.append(r.text)
            lines.append("-" * 40)

        return "\n".join(lines)
