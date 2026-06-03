"""End-to-end multi-agent pipeline verification test."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.logger import setup_logging
from app.db.redis_db import RedisClient
from app.db.vector_db import VectorDBClient
from app.services.llm_service import LLMService
from app.services.sql_service import SQLService
from app.services.cache_service import CacheService
from app.services.rag_service import RAGService

# Agents
from app.agents.intent_agent import IntentAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.sql_generation_agent import SQLGenerationAgent
from app.agents.sql_validation_agent import SQLValidationAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.insight_agent import InsightAgent
from app.agents.summarization_agent import SummarizationAgent
from app.agents.orchestration_agent import OrchestrationAgent

from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.vector_store import VectorStore
from app.rag.retriever import SchemaRetriever
from app.rag.reranker import Reranker


async def run_pipeline(user_query: str) -> None:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)

    print("=" * 60)
    print(f"Testing End-to-End Pipeline for query: {user_query!r}")
    print("=" * 60)

    # Database
    db_engine = create_async_engine(settings.DATABASE_URL)
    
    # Redis
    redis_client = RedisClient(settings.REDIS_URL)
    await redis_client.connect()

    # Qdrant
    qdrant_wrapper = VectorDBClient(
        url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION,
    )
    await qdrant_wrapper.connect()

    try:
        # LLM Client
        llm_service = LLMService(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
            embedding_model=settings.EMBEDDING_MODEL,
        )

        sql_service = SQLService(engine=db_engine)
        cache_service = CacheService(redis_client=redis_client)

        # RAG pipeline setup
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
        
        rag_service = RAGService(
            schema_indexer=None,
            retriever=retriever,
            reranker=reranker,
        )

        # Agent pipelines
        intent_agent = IntentAgent(llm_service=llm_service)
        retrieval_agent = RetrievalAgent(retriever=retriever, reranker=reranker)

        sql_generation_agent = SQLGenerationAgent(llm_service=llm_service)
        sql_validation_agent = SQLValidationAgent()
        visualization_agent = VisualizationAgent(llm_service=llm_service)
        insight_agent = InsightAgent(llm_service=llm_service)
        summarization_agent = SummarizationAgent(llm_service=llm_service)

        orchestration_agent = OrchestrationAgent(
            intent_agent=intent_agent,
            retrieval_agent=retrieval_agent,
            sql_generation_agent=sql_generation_agent,
            sql_validation_agent=sql_validation_agent,
            visualization_agent=visualization_agent,
            insight_agent=insight_agent,
            summarization_agent=summarization_agent,
            sql_service=sql_service,
            cache_service=cache_service,
        )

        print("\nStarting pipeline execution...")
        response = await orchestration_agent.process_message(
            user_message=user_query,
            user_id=1,
            conversation_id=999,
        )

        print("\nPIPELINE EXECUTION COMPLETE!")
        print("=" * 60)
        print("Message Output:")
        print(response.message)
        print("-" * 60)
        if response.sql_query:
            print("Generated & Executed SQL:")
            print(response.sql_query)
        if response.query_results:
            print(f"Query Results Row Count: {len(response.query_results)}")
        if response.visualizations:
            print(f"Generated Visualizations: {len(response.visualizations)}")
            for idx, viz in enumerate(response.visualizations):
                print(f"  Chart {idx+1}: {viz.title} ({viz.chart_type})")
        if response.insights:
            print("\nGenerated AI Insights:")
            print(f"Summary: {response.insights.summary}")
            print(f"Trends: {response.insights.trends}")
            print(f"Anomalies: {response.insights.anomalies}")
        if response.follow_up_suggestions:
            print("\nSuggested Follow-up Queries:")
            for s in response.follow_up_suggestions:
                print(f"  - {s}")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR: Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await redis_client.close()
        await qdrant_wrapper.close()
        await db_engine.dispose()


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Show me total sales across regions"
    asyncio.run(run_pipeline(query))
