"""Main FastAPI Application Entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import get_settings
from app.core.logger import setup_logging
from app.core.middleware import LoggingMiddleware, RateLimitMiddleware, RequestIDMiddleware
from app.core.exceptions import register_exception_handlers
from app.observability.metrics import MetricsMiddleware

# Routers
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.chat_routes import router as chat_router
from app.api.v1.dashboard_routes import router as dashboard_router
from app.api.v1.sql_routes import router as sql_router
from app.api.v1.health_routes import router as health_router

# Core components
from app.db.redis_db import RedisClient
from app.db.vector_db import VectorDBClient
from app.services.llm_service import LLMService
from app.services.sql_service import SQLService
from app.services.cache_service import CacheService
from app.services.rag_service import RAGService
from app.services.chat_service import ChatService
from app.services.dashboard_service import DashboardService

# Agents
from app.agents.intent_agent import IntentAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.sql_generation_agent import SQLGenerationAgent
from app.agents.sql_validation_agent import SQLValidationAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.insight_agent import InsightAgent
from app.agents.summarization_agent import SummarizationAgent
from app.agents.orchestration_agent import OrchestrationAgent

# RAG pieces
from app.rag.schema_indexer import SchemaIndexer
from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.vector_store import VectorStore
from app.rag.retriever import SchemaRetriever
from app.rag.reranker import Reranker

# Repositories
from app.repositories.chat_repository import ChatRepository
from app.repositories.dashboard_repository import DashboardRepository
import app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 1. Setup config & logger ─────────────────────────────────────
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger("app.main")
    logger.info("Initializing RAG-based ChatBOT services...")

    # ── 2. Initialize Database engine & session maker ────────────────
    db_engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        db_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    app.state.db_engine = db_engine
    app.state.session_factory = session_factory

    # ── Create tables dynamically if they don't exist ────────────────
    from app.db.base import Base
    async with db_engine.begin() as conn:
        logger.info("Creating all database tables (if they do not exist)...")
        await conn.run_sync(Base.metadata.create_all)



    # ── 3. Connect Redis ─────────────────────────────────────────────
    redis_client = RedisClient(settings.REDIS_URL)
    await redis_client.connect()
    app.state.redis_client = redis_client

    # ── 4. Connect Qdrant Client ─────────────────────────────────────
    qdrant_client_wrapper = VectorDBClient(
        url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION,
    )
    await qdrant_client_wrapper.connect()
    app.state.qdrant_client = qdrant_client_wrapper

    # ── 5. Initialize Services ───────────────────────────────────────
    llm_service = LLMService(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        embedding_model=settings.EMBEDDING_MODEL,
    )
    app.state.llm_service = llm_service

    sql_service = SQLService(engine=db_engine)
    app.state.sql_service = sql_service

    cache_service = CacheService(redis_client=redis_client)
    app.state.cache_service = cache_service

    # RAG pipeline setup
    embedding_generator = EmbeddingGenerator(
        api_key=settings.GEMINI_API_KEY,
        model=settings.EMBEDDING_MODEL,
    )
    
    # We retrieve the raw synchronous client underlying the Qdrant client wrapper
    vector_store = VectorStore(
        client=qdrant_client_wrapper.client,
        collection_name=settings.QDRANT_COLLECTION,
    )
    
    schema_indexer = SchemaIndexer(
        engine=db_engine,
        embedding_generator=embedding_generator,
        vector_store=vector_store,
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
        schema_indexer=schema_indexer,
        retriever=retriever,
        reranker=reranker,
    )
    app.state.rag_service = rag_service

    # ── 6. Initialize Agents ──────────────────────────────────────────
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

    # ── 7. Repository layers & top level services ─────────────────────
    # We instantiate these using a mock or a transient session (repo internally does db calls per query)
    # The repositories themselves will receive session inside routes, but here we can create
    # the master services by instantiating them with session-aware repositories or standard factories
    async with session_factory() as startup_session:
        chat_repo = ChatRepository(startup_session)
        dashboard_repo = DashboardRepository(startup_session)
        
    chat_service = ChatService(
        chat_repo=ChatRepository(None), # repositories will be bound to current session per request
        orchestration_agent=orchestration_agent,
        summarization_agent=summarization_agent,
    )
    app.state.chat_service = chat_service

    dashboard_service = DashboardService(
        dashboard_repo=DashboardRepository(None),
    )
    app.state.dashboard_service = dashboard_service

    # We patch services to retrieve current request sessions dynamically or pass a bound repo
    # To enable repository pattern with request-scoped session, we will wrap/bind repositories in dependencies
    # Wait, let's see how our services and routes use this!
    # In chat_routes: chat_svc receives `Depends(get_chat_service)`. Let's create a request-bound
    # ChatService inside get_chat_service dependency to inject the current DB session! That is extremely clean.
    # Let's verify: yes, get_chat_service should bind the request scoped DB session to ChatRepository.
    # Let's adjust app/core/dependencies.py to do exactly that!
    
    logger.info("RAG-based ChatBOT services initialized successfully.")
    
    yield

    # ── 8. Shutdown logic ─────────────────────────────────────────────
    logger.info("Shutting down RAG-based ChatBOT services...")
    await redis_client.close()
    await qdrant_client_wrapper.close()
    await db_engine.dispose()
    logger.info("Shutdown complete.")


settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Exception handlers
register_exception_handlers(app)

# Middlewares
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers inclusion
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(sql_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
