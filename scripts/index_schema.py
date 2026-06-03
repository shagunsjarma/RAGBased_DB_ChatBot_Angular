"""Script to introspect database schema and index it into Qdrant."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.logger import setup_logging
from app.db.vector_db import VectorDBClient
from app.rag.schema_indexer import SchemaIndexer
from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.vector_store import VectorStore


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    
    print("Starting MySQL Schema Indexer...")
    print(f"Database URL: {settings.DATABASE_URL.split('@')[-1]}")
    print(f"Qdrant URL: {settings.QDRANT_URL}")
    print(f"Collection: {settings.QDRANT_COLLECTION}")

    # Initialize MySQL engine
    db_engine = create_async_engine(settings.DATABASE_URL)

    # Initialize Qdrant connection
    qdrant_wrapper = VectorDBClient(
        url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION,
    )
    await qdrant_wrapper.connect()

    try:
        # Check health
        if not await qdrant_wrapper.health_check():
            print("ERROR: Qdrant service is down or unreachable.")
            return

        # Core pipeline components
        embedding_generator = EmbeddingGenerator(
            api_key=settings.GEMINI_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
        
        vector_store = VectorStore(
            client=qdrant_wrapper.client,
            collection_name=settings.QDRANT_COLLECTION,
        )
        
        schema_indexer = SchemaIndexer(
            engine=db_engine,
            embedding_generator=embedding_generator,
            vector_store=vector_store,
        )

        print("Executing full database introspection and schema indexing...")
        stats = await schema_indexer.index_database_schema()
        print("\nINDEXING COMPLETE!")
        print("-" * 30)
        print(f"Tables Indexed:   {stats.get('tables_indexed')}")
        print(f"Chunks Created:   {stats.get('chunks_created')}")
        print(f"Vectors Stored:   {stats.get('vectors_stored')}")
        print("-" * 30)

    except Exception as e:
        print(f"ERROR: Indexing failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        await qdrant_wrapper.close()
        await db_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
