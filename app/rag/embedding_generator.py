"""Embedding generation via Google Gemini."""

from __future__ import annotations

import asyncio

import google.generativeai as genai

from app.core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate text embeddings using Google Gemini embedding models."""

    def __init__(self, api_key: str, model: str = "models/embedding-001") -> None:
        genai.configure(api_key=api_key)
        self._model = model

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate a single embedding vector."""
        text = self._prepare_text(text)
        result = await asyncio.to_thread(
            genai.embed_content, model=self._model, content=text, task_type="retrieval_document",
        )
        return result["embedding"]

    async def generate_embeddings_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = [self._prepare_text(t) for t in texts[i:i + batch_size]]
            result = await asyncio.to_thread(
                genai.embed_content, model=self._model, content=batch, task_type="retrieval_document",
            )
            all_embeddings.extend(result["embedding"])
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)  # Rate limiting
        return all_embeddings

    async def generate_query_embedding(self, text: str) -> list[float]:
        """Generate embedding for a search query (uses retrieval_query task)."""
        text = self._prepare_text(text)
        result = await asyncio.to_thread(
            genai.embed_content, model=self._model, content=text, task_type="retrieval_query",
        )
        return result["embedding"]

    def _prepare_text(self, text: str) -> str:
        """Clean and truncate text."""
        text = " ".join(text.split())  # normalize whitespace
        return text[:8000]  # rough truncation
