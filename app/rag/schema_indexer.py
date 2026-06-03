"""Schema indexer – introspects MySQL and indexes into Qdrant."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.rag.chunking import SchemaChunker
from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.vector_store import VectorStore
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)


class SchemaIndexer:
    """Connects to MySQL, introspects schema, and indexes into the vector store."""

    def __init__(self, engine: AsyncEngine, embedding_generator: EmbeddingGenerator, vector_store: VectorStore) -> None:
        self._engine = engine
        self._embedder = embedding_generator
        self._vector_store = vector_store
        self._chunker = SchemaChunker()

    async def index_database_schema(self) -> dict[str, int]:
        """Full pipeline: introspect → chunk → embed → upsert. Returns stats."""
        await self._vector_store.ensure_collection(vector_size=get_settings().EMBEDDING_DIMENSION)


        tables = await self.get_all_tables()
        all_chunks: list[dict[str, Any]] = []

        for table_name in tables:
            info = await self.get_table_info(table_name)
            description = self._format_table_description(
                table_name, info["columns"], info["foreign_keys"], info["indexes"], info["sample_rows"],
            )
            chunks = self._chunker.chunk_table(table_name, description, info["columns"], info["foreign_keys"])
            all_chunks.extend(chunks)

        # Full schema overview chunk
        overview = self._chunker.chunk_full_schema(tables)
        all_chunks.append(overview)

        # Generate embeddings
        texts = [c["text"] for c in all_chunks]
        embeddings = await self._embedder.generate_embeddings_batch(texts)

        # Prepare and upsert vectors
        vectors = [
            {"id": str(uuid.uuid4()), "vector": emb, "payload": {"text": c["text"], **c["metadata"]}}
            for c, emb in zip(all_chunks, embeddings)
        ]
        count = await self._vector_store.upsert(vectors)

        stats = {"tables_indexed": len(tables), "chunks_created": len(all_chunks), "vectors_stored": count}
        logger.info("schema_indexed", **stats)
        return stats

    async def get_all_tables(self) -> list[str]:
        async with self._engine.connect() as conn:
            tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        return tables

    async def get_table_info(self, table_name: str) -> dict[str, Any]:
        async with self._engine.connect() as conn:
            columns = await conn.run_sync(lambda c: inspect(c).get_columns(table_name))
            fks = await conn.run_sync(lambda c: inspect(c).get_foreign_keys(table_name))
            indexes = await conn.run_sync(lambda c: inspect(c).get_indexes(table_name))

            # Sample rows
            result = await conn.execute(text(f"SELECT * FROM `{table_name}` LIMIT 5"))
            sample_rows = [dict(row._mapping) for row in result.fetchall()]

        return {"columns": columns, "foreign_keys": fks, "indexes": indexes, "sample_rows": sample_rows}

    def _format_table_description(self, table_name: str, columns: list, fks: list, indexes: list, sample_rows: list) -> str:
        lines = [f"Table: {table_name}", "Columns:"]
        for col in columns:
            pk = ", PRIMARY KEY" if col.get("primary_key") else ""
            nullable = ", NOT NULL" if not col.get("nullable", True) else ""
            default = f", DEFAULT={col['default']}" if col.get("default") else ""
            lines.append(f"  - {col['name']} ({col['type']}{pk}{nullable}{default})")

        if fks:
            lines.append("Foreign Keys:")
            for fk in fks:
                ref = f"{fk['referred_table']}.{','.join(fk['referred_columns'])}"
                lines.append(f"  - {','.join(fk['constrained_columns'])} -> {ref}")

        if indexes:
            lines.append("Indexes:")
            for idx in indexes:
                lines.append(f"  - {idx['name']} ({','.join(idx['column_names'])})")

        if sample_rows:
            lines.append("Sample Data (first 5 rows):")
            if sample_rows:
                headers = list(sample_rows[0].keys())
                lines.append("  | " + " | ".join(headers) + " |")
                for row in sample_rows[:3]:
                    lines.append("  | " + " | ".join(str(row.get(h, ""))[:30] for h in headers) + " |")

        return "\n".join(lines)
