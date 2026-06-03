"""Reranker – uses Gemini to re-score retrieval results by relevance."""

from __future__ import annotations

import json

import google.generativeai as genai

from app.rag.retriever import RetrievalResult
from app.core.logger import get_logger

logger = get_logger(__name__)


class Reranker:
    """Re-ranks retrieval results using an LLM relevance score."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    async def rerank(self, query: str, results: list[RetrievalResult], top_k: int = 5) -> list[RetrievalResult]:
        """Re-rank results and return the top-k most relevant."""
        if len(results) <= top_k:
            return results

        try:
            prompt = self._build_rerank_prompt(query, results)
            response = await self._model.generate_content_async(prompt)
            text = response.text.strip()

            # Parse scores
            if text.startswith("```"):
                text = text.split("```")[1].strip()
                if text.startswith("json"):
                    text = text[4:].strip()

            scores = json.loads(text)
            for i, result in enumerate(results):
                if i < len(scores):
                    result.score = float(scores[i]) / 10.0

            results.sort(key=lambda r: r.score, reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.warning("rerank_failed", error=str(e))
            # Fallback: return top-k by original score
            return sorted(results, key=lambda r: r.score, reverse=True)[:top_k]

    def _build_rerank_prompt(self, query: str, results: list[RetrievalResult]) -> str:
        contexts = "\n\n".join(
            f"[Context {i}] (table: {r.table_name}):\n{r.text[:500]}"
            for i, r in enumerate(results)
        )
        return f"""Rate the relevance of each database schema context to the user query on a scale of 0-10.
Return ONLY a JSON array of numbers, one per context. Example: [8, 3, 9, 1, 5]

User Query: {query}

{contexts}

Relevance scores (JSON array of {len(results)} numbers):"""
