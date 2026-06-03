"""Qdrant vector database client wrapper."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import get_settings


class VectorDBClient:
    """Thin async-friendly wrapper around the synchronous ``QdrantClient``."""

    def __init__(self, url: str | None = None, collection_name: str | None = None) -> None:
        settings = get_settings()
        self._url = url or settings.QDRANT_URL
        self._collection = collection_name or settings.QDRANT_COLLECTION
        self._client: QdrantClient | None = None

    # ── Lifecycle ────────────────────────────────────────────────────
    async def connect(self) -> None:
        self._client = await asyncio.to_thread(QdrantClient, url=self._url)

    async def close(self) -> None:
        if self._client is not None:
            await asyncio.to_thread(self._client.close)
            self._client = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            raise RuntimeError("VectorDBClient not connected. Call connect() first.")
        return self._client

    # ── Collection management ────────────────────────────────────────
    async def create_collection(
        self, vector_size: int = 768, distance: Distance = Distance.COSINE,
    ) -> None:
        collections = await asyncio.to_thread(self.client.get_collections)
        existing = [c.name for c in collections.collections]
        if self._collection not in existing:
            await asyncio.to_thread(
                self.client.create_collection,
                collection_name=self._collection,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )

    async def delete_collection(self) -> None:
        await asyncio.to_thread(self.client.delete_collection, collection_name=self._collection)

    async def collection_info(self) -> dict[str, Any]:
        info = await asyncio.to_thread(self.client.get_collection, collection_name=self._collection)
        return {"points_count": info.points_count, "status": info.status.value}

    # ── CRUD ─────────────────────────────────────────────────────────
    async def upsert_vectors(self, vectors: list[dict[str, Any]]) -> int:
        """Upsert vectors. Each dict must have ``id``, ``vector``, ``payload``."""
        points = [
            PointStruct(
                id=v.get("id", str(uuid.uuid4())),
                vector=v["vector"],
                payload=v.get("payload", {}),
            )
            for v in vectors
        ]
        await asyncio.to_thread(
            self.client.upsert,
            collection_name=self._collection,
            points=points,
        )
        return len(points)

    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        table_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        query_filter = None
        if table_filter:
            query_filter = Filter(
                must=[FieldCondition(key="table_name", match=MatchValue(value=table_filter))]
            )
        results = await asyncio.to_thread(
            self.client.search,
            collection_name=self._collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        return [
            {
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "table_name": hit.payload.get("table_name", ""),
                "chunk_type": hit.payload.get("chunk_type", ""),
            }
            for hit in results
        ]

    # ── Health ───────────────────────────────────────────────────────
    async def health_check(self) -> bool:
        try:
            await asyncio.to_thread(self.client.get_collections)
            return True
        except Exception:
            return False
