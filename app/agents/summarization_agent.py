"""Summarization agent – creates final responses and follow-up suggestions."""

from __future__ import annotations

import json

from app.prompts.summarization_prompt import (
    RESPONSE_SUMMARIZATION_PROMPT, FOLLOW_UP_PROMPT, CONVERSATION_TITLE_PROMPT,
)
from app.core.logger import get_logger

logger = get_logger(__name__)


class SummarizationAgent:
    """Generates natural language summaries and follow-up suggestions."""

    def __init__(self, llm_service) -> None:
        self._llm = llm_service

    async def summarize_response(self, sql: str, results_summary: str,
                                  insights: dict, chart_descriptions: list[str]) -> str:
        prompt = RESPONSE_SUMMARIZATION_PROMPT.format(
            sql_query=sql, results_summary=results_summary,
            chart_descriptions=", ".join(chart_descriptions) if chart_descriptions else "No charts",
            insights=json.dumps(insights, default=str),
        )
        try:
            return await self._llm.generate(prompt, temperature=0.3)
        except Exception as e:
            logger.warning("summarization_failed", error=str(e))
            return results_summary

    async def generate_follow_ups(self, query: str, results_summary: str,
                                   chat_history: list[dict] | None = None) -> list[str]:
        history_text = ""
        if chat_history:
            history_text = "\n".join(f"{m['role']}: {m['content']}" for m in chat_history[-5:])

        prompt = FOLLOW_UP_PROMPT.format(
            query=query, results_summary=results_summary, chat_history=history_text,
        )
        try:
            result = await self._llm.generate_json(prompt)
            if isinstance(result, list):
                return result[:5]
            return []
        except Exception:
            return [
                "Can you break this down by month?",
                "What about the top 10 results?",
                "Show me the trend over time",
            ]

    async def generate_title(self, first_message: str) -> str:
        prompt = CONVERSATION_TITLE_PROMPT.format(message=first_message)
        try:
            title = await self._llm.generate(prompt, temperature=0.3)
            return title.strip().strip('"')[:50]
        except Exception:
            return first_message[:50]
