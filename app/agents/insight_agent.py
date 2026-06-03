"""Insight agent – generates data insights via stats + LLM."""

from __future__ import annotations

import json

from app.prompts.insight_prompt import INSIGHT_GENERATION_PROMPT
from app.schemas.chat_schema import InsightData
from app.core.logger import get_logger

logger = get_logger(__name__)


class InsightAgent:
    """Generates statistical and LLM-powered insights from query results."""

    def __init__(self, llm_service) -> None:
        self._llm = llm_service

    async def generate_insights(self, query: str, columns: list[str],
                                 data: list[dict], sql: str) -> InsightData:
        stats = self._calculate_summary_stats(data, columns)
        sample = data[:5] if data else []

        prompt = INSIGHT_GENERATION_PROMPT.format(
            sql_query=sql, columns=columns,
            stats=json.dumps(stats, default=str),
            sample_data=json.dumps(sample, default=str),
            row_count=len(data),
        )

        try:
            result = await self._llm.generate_json(prompt)
            return InsightData(
                summary=result.get("summary", "No insights available."),
                trends=result.get("trends", []),
                anomalies=result.get("anomalies", []),
                recommendations=result.get("recommendations", []),
            )
        except Exception as e:
            logger.warning("insight_generation_failed", error=str(e))
            return InsightData(
                summary=f"Query returned {len(data)} rows across {len(columns)} columns.",
                trends=[], anomalies=[], recommendations=[],
            )

    def _calculate_summary_stats(self, data: list[dict], columns: list[str]) -> dict:
        stats = {}
        for col in columns:
            values = []
            for row in data:
                v = row.get(col)
                if v is not None:
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        continue
            if values:
                values.sort()
                n = len(values)
                stats[col] = {
                    "count": n, "min": min(values), "max": max(values),
                    "mean": round(sum(values) / n, 2),
                    "median": values[n // 2],
                }
        return stats
