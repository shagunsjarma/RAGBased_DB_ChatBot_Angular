"""LLM Service – Google Gemini client wrapper."""

from __future__ import annotations

import json
import asyncio

import google.generativeai as genai

from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Wrapper around Google Gemini for text generation and embeddings."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash",
                 embedding_model: str = "models/embedding-001") -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._model_name = model
        self._embedding_model = embedding_model

    async def generate(self, prompt: str, system_prompt: str | None = None,
                       temperature: float = 0.1, max_tokens: int = 4096) -> str:
        """Generate text from a prompt."""
        config = genai.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens)

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        try:
            response = await self._model.generate_content_async(
                contents, generation_config=config,
            )
            return response.text.strip()
        except Exception as e:
            logger.error("llm_generate_failed", error=str(e))
            raise

    async def generate_json(self, prompt: str, system_prompt: str | None = None) -> dict | list:
        """Generate and parse JSON response. Strips markdown fences."""
        raw = await self.generate(prompt, system_prompt=system_prompt, temperature=0.1)

        # Strip markdown code fences
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        return json.loads(text)

    async def generate_with_history(self, messages: list[dict], system_prompt: str | None = None) -> str:
        """Multi-turn conversation. Messages: [{role, content}]."""
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})

        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        response = await self._model.generate_content_async(contents)
        return response.text.strip()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate a single embedding vector."""
        result = await asyncio.to_thread(
            genai.embed_content, model=self._embedding_model,
            content=text, task_type="retrieval_document",
        )
        return result["embedding"]

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding generation."""
        all_emb: list[list[float]] = []
        for i in range(0, len(texts), 100):
            batch = texts[i:i + 100]
            result = await asyncio.to_thread(
                genai.embed_content, model=self._embedding_model,
                content=batch, task_type="retrieval_document",
            )
            all_emb.extend(result["embedding"])
            if i + 100 < len(texts):
                await asyncio.sleep(0.5)
        return all_emb

    async def count_tokens(self, text: str) -> int:
        """Count tokens for text."""
        try:
            result = await self._model.count_tokens_async(text)
            return result.total_tokens
        except Exception:
            return len(text.split()) * 2  # rough estimate

    async def health_check(self) -> bool:
        """Verify API key works."""
        try:
            await self.generate("Say OK", temperature=0.0, max_tokens=5)
            return True
        except Exception:
            return False
