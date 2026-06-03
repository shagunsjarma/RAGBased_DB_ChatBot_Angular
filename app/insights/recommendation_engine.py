"""Recommendation engine – follow-up suggestions via LLM."""

from __future__ import annotations


class RecommendationEngine:
    def __init__(self, llm_service) -> None:
        self._llm = llm_service

    async def generate_recommendations(self, query: str, results_summary: str,
                                        chat_history: list[dict] | None = None) -> list[str]:
        prompt = f"""Based on this query and results, suggest 3-5 follow-up analyses:
Query: {query}
Results: {results_summary}

Return a JSON array of suggestion strings."""
        try:
            result = await self._llm.generate_json(prompt)
            return result if isinstance(result, list) else []
        except Exception:
            return ["Drill down by time period", "Compare across categories", "Look at top/bottom performers"]

    async def suggest_related_tables(self, current_tables: list[str],
                                      all_tables: list[str]) -> list[str]:
        other = [t for t in all_tables if t not in current_tables]
        return other[:5]
