"""RAG service – schema indexing and retrieval orchestration."""

from __future__ import annotations

from app.rag.schema_indexer import SchemaIndexer
from app.rag.retriever import SchemaRetriever
from app.rag.reranker import Reranker
from app.core.constants import RERANKER_TOP_K


class RAGService:
    def __init__(self, schema_indexer: SchemaIndexer,
                 retriever: SchemaRetriever, reranker: Reranker) -> None:
        self._indexer = schema_indexer
        self._retriever = retriever
        self._reranker = reranker

    async def index_schema(self) -> dict:
        return await self._indexer.index_database_schema()

    async def retrieve_context(self, query: str, top_k: int = 10) -> str:
        results = await self._retriever.retrieve(query, top_k=top_k)
        results = await self._reranker.rerank(query, results, top_k=RERANKER_TOP_K)
        return self._retriever.format_context(results)

    async def reindex(self) -> dict:
        from app.rag.vector_store import VectorStore
        # The indexer handles creating a fresh collection
        return await self._indexer.index_database_schema()

    async def get_index_stats(self) -> dict:
        return await self._indexer._vector_store.get_collection_stats()
