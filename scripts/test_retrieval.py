"""Script to test hybrid retrieval from Qdrant."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.db.vector_db import VectorDBClient
from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.vector_store import VectorStore
from app.rag.retriever import SchemaRetriever
from app.rag.reranker import Reranker


async def test_retrieve(query: str) -> None:
    settings = get_settings()
    
    print(f"Testing retrieval for query: {query!r}\n")
    
    qdrant_wrapper = VectorDBClient(
        url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION,
    )
    await qdrant_wrapper.connect()

    try:
        embedding_generator = EmbeddingGenerator(
            api_key=settings.GEMINI_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
        
        vector_store = VectorStore(
            client=qdrant_wrapper.client,
            collection_name=settings.QDRANT_COLLECTION,
        )
        
        retriever = SchemaRetriever(
            embedding_generator=embedding_generator,
            vector_store=vector_store,
        )
        
        reranker = Reranker(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
        )

        print("Executing retriever search...")
        results = await retriever.retrieve(query, top_k=6)
        print(f"Retrieved {len(results)} chunks.")
        for i, r in enumerate(results):
            print(f"  [{i+1}] Score: {r.score:.4f} | Table: {r.table_name} | Type: {r.chunk_type}")

        print("\nExecuting Reranker (Gemini cross-encoder re-score)...")
        reranked = await reranker.rerank(query, results, top_k=3)
        print(f"Top {len(reranked)} Reranked Context Chunks:")
        print("=" * 60)
        print(retriever.format_context(reranked))
        print("=" * 60)

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await qdrant_wrapper.close()


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Show me active users registered last week"
    asyncio.run(test_retrieve(query))
