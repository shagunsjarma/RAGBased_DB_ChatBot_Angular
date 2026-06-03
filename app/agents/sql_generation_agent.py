"""SQL generation agent – translates NL to SQL via Gemini."""

from __future__ import annotations

import re

from app.prompts.sql_prompt import SQL_GENERATION_SYSTEM_PROMPT, SQL_GENERATION_USER_PROMPT, FEW_SHOT_TEMPLATE
from app.schemas.sql_schema import SQLGenerationResult
from app.core.logger import get_logger

logger = get_logger(__name__)


class SQLGenerationAgent:
    """Generates MySQL queries from natural language using Gemini."""

    def __init__(self, llm_service) -> None:
        self._llm = llm_service

    async def generate_sql(self, user_query: str, schema_context: str,
                            chat_history: list[dict] | None = None,
                            few_shot_examples: list[dict] | None = None) -> SQLGenerationResult:
        # Format chat history
        history_text = "No previous conversation."
        if chat_history:
            history_text = "\n".join(f"{m['role']}: {m['content']}" for m in chat_history[-5:])

        # Format few-shot examples
        examples_text = "No similar past queries."
        if few_shot_examples:
            examples_text = "\n\n".join(
                FEW_SHOT_TEMPLATE.format(question=e.get("question", ""), sql=e.get("sql", ""), summary=e.get("summary", ""))
                for e in few_shot_examples[:3]
            )

        prompt = SQL_GENERATION_USER_PROMPT.format(
            schema_context=schema_context,
            chat_history=history_text,
            few_shot_examples=examples_text,
            user_question=user_query,
        )

        try:
            response = await self._llm.generate(prompt, system_prompt=SQL_GENERATION_SYSTEM_PROMPT, temperature=0.1)
            sql = self._clean_sql(response)

            # Extract table names from SQL
            tables = self._extract_tables(sql)

            return SQLGenerationResult(
                sql_query=sql,
                confidence=0.85,
                explanation=f"Generated SQL to answer: {user_query}",
                tables_used=tables,
            )
        except Exception as e:
            logger.error("sql_generation_failed", error=str(e))
            return SQLGenerationResult(
                sql_query="",
                confidence=0.0,
                explanation=f"Failed to generate SQL: {e}",
                tables_used=[],
            )

    def _clean_sql(self, response: str) -> str:
        """Strip markdown fences and clean up the SQL."""
        sql = response.strip()
        # Remove markdown code fences
        if sql.startswith("```"):
            lines = sql.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            sql = "\n".join(lines).strip()
        # Remove trailing semicolons
        sql = sql.rstrip(";").strip()
        return sql

    def _extract_tables(self, sql: str) -> list[str]:
        """Extract table names from SQL using simple regex."""
        pattern = r'\b(?:FROM|JOIN)\s+`?(\w+)`?'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        return list(set(matches))
