"""Executive summary generation via LLM."""

from __future__ import annotations

import json
from app.prompts.insight_prompt import EXECUTIVE_SUMMARY_PROMPT


class ExecutiveSummary:
    def __init__(self, llm_service) -> None:
        self._llm = llm_service

    async def generate(self, query: str, data: list[dict], columns: list[str], stats: dict) -> str:
        metrics = json.dumps(stats, default=str)
        prompt = EXECUTIVE_SUMMARY_PROMPT.format(
            query=query, metrics=metrics, row_count=len(data),
        )
        return await self._llm.generate(prompt, temperature=0.3)

    def _prepare_stats(self, data: list[dict], columns: list[str]) -> dict:
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
                stats[col] = {
                    "count": len(values), "min": min(values), "max": max(values),
                    "mean": round(sum(values) / len(values), 2),
                    "sum": round(sum(values), 2),
                }
        return stats
