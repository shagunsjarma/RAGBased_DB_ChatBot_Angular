"""Script to delete vector collection or clean up specific tables."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.db.vector_db import VectorDBClient


async def main() -> None:
    settings = get_settings()
    
    collection = settings.QDRANT_COLLECTION
    table_name = sys.argv[1] if len(sys.argv) > 1 else None

    qdrant_wrapper = VectorDBClient(
        url=settings.QDRANT_URL,
        collection_name=collection,
    )
    await qdrant_wrapper.connect()

    try:
        if table_name:
            print(f"Deleting vectors for table {table_name!r} from collection {collection}...")
            # We can use the sync client underneath
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            await asyncio.to_thread(
                qdrant_wrapper.client.delete,
                collection_name=collection,
                points_selector=Filter(
                    must=[FieldCondition(key="table_name", match=MatchValue(value=table_name))]
                )
            )
            print(f"Vectors for table {table_name!r} deleted.")
        else:
            print(f"Deleting the entire collection {collection}...")
            await qdrant_wrapper.delete_collection()
            print("Collection deleted.")
            
    except Exception as e:
        print(f"ERROR: Cleanup failed: {e}")
    finally:
        await qdrant_wrapper.close()


if __name__ == "__main__":
    asyncio.run(main())
