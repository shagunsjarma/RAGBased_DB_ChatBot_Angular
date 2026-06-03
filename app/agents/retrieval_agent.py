"""Retrieval agent – fetches schema context via RAG."""

from __future__ import annotations

from app.agents.intent_agent import IntentResult
from app.rag.retriever import SchemaRetriever
from app.rag.reranker import Reranker
from app.core.constants import TOP_K_RETRIEVAL, RERANKER_TOP_K
from app.core.logger import get_logger

logger = get_logger(__name__)


class RetrievalAgent:
    """Retrieves and reranks schema context based on classified intent."""

    def __init__(self, retriever: SchemaRetriever, reranker: Reranker) -> None:
        self._retriever = retriever
        self._reranker = reranker

    async def retrieve_context(self, intent_result: IntentResult, chat_history: list[dict] | None = None) -> str:
        query = intent_result.rewritten_query or "database schema"
        tables = intent_result.entities.get("tables", [])

        if tables:
            results = await self._retriever.retrieve_for_tables(tables)
            # Also do a general query to catch related tables
            general = await self._retriever.retrieve(query, top_k=TOP_K_RETRIEVAL)
            # Merge, deduplicate by table_name + chunk_type
            seen = {(r.table_name, r.chunk_type) for r in results}
            for r in general:
                if (r.table_name, r.chunk_type) not in seen:
                    results.append(r)
                    seen.add((r.table_name, r.chunk_type))
        else:
            results = await self._retriever.retrieve(query, top_k=TOP_K_RETRIEVAL)

        # Rerank
        if len(results) > RERANKER_TOP_K:
            results = await self._reranker.rerank(query, results, top_k=RERANKER_TOP_K)

        context = self._retriever.format_context(results)
        logger.info("context_retrieved", chunks=len(results), tables=list({r.table_name for r in results}))
        return context
