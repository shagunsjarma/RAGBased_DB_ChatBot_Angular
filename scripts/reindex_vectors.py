"""Script to clear the Qdrant collection and re-index the schema."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.db.vector_db import VectorDBClient
from scripts.index_schema import main as index_main


async def main() -> None:
    settings = get_settings()
    
    print("WARNING: This will clear the entire vector collection and re-index!")
    qdrant_wrapper = VectorDBClient(
        url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION,
    )
    await qdrant_wrapper.connect()

    try:
        print(f"Deleting collection: {settings.QDRANT_COLLECTION}...")
        await qdrant_wrapper.delete_collection()
        print("Collection deleted successfully.")
    except Exception as e:
        print(f"Collection delete skipped/failed: {e}")
    finally:
        await qdrant_wrapper.close()

    # Re-run standard schema indexing
    await index_main()


if __name__ == "__main__":
    asyncio.run(main())
