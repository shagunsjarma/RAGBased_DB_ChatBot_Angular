"""Qdrant vector store operations."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, Filter, FieldCondition, MatchValue, PointStruct, VectorParams

from app.core.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Wrapper for Qdrant vector operations."""

    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        self._client = client
        self._collection = collection_name

    async def ensure_collection(self, vector_size: int = 768) -> None:
        """Create collection if it does not exist."""
        collections = await asyncio.to_thread(self._client.get_collections)
        existing = [c.name for c in collections.collections]
        if self._collection not in existing:
            await asyncio.to_thread(
                self._client.create_collection,
                collection_name=self._collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("collection_created", collection=self._collection)

    async def upsert(self, chunks: list[dict[str, Any]]) -> int:
        """Upsert vectors. Each dict: {id, vector, payload}."""
        points = [
            PointStruct(id=c.get("id", str(uuid.uuid4())), vector=c["vector"], payload=c.get("payload", {}))
            for c in chunks
        ]
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            await asyncio.to_thread(self._client.upsert, collection_name=self._collection, points=batch)
        return len(points)

    async def search(self, query_vector: list[float], limit: int = 10, table_filter: str | None = None) -> list[dict[str, Any]]:
        query_filter = None
        if table_filter:
            query_filter = Filter(must=[FieldCondition(key="table_name", match=MatchValue(value=table_filter))])

        results = await asyncio.to_thread(
            self._client.search, collection_name=self._collection,
            query_vector=query_vector, limit=limit, query_filter=query_filter,
        )
        return [
            {"text": h.payload.get("text", ""), "score": h.score,
             "table_name": h.payload.get("table_name", ""), "chunk_type": h.payload.get("chunk_type", "")}
            for h in results
        ]

    async def delete_by_table(self, table_name: str) -> None:
        await asyncio.to_thread(
            self._client.delete, collection_name=self._collection,
            points_selector=Filter(must=[FieldCondition(key="table_name", match=MatchValue(value=table_name))]),
        )

    async def get_collection_stats(self) -> dict[str, Any]:
        info = await asyncio.to_thread(self._client.get_collection, collection_name=self._collection)
        return {"points_count": info.points_count, "status": info.status.value}
