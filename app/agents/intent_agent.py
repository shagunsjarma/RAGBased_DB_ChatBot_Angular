"""Intent classification agent."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.core.constants import IntentType
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IntentResult:
    intent_type: IntentType
    entities: dict = field(default_factory=dict)
    confidence: float = 0.0
    rewritten_query: str = ""


class IntentAgent:
    """Classifies user intent and extracts entities using Gemini."""

    def __init__(self, llm_service) -> None:
        self._llm = llm_service

    async def classify_intent(self, message: str, chat_history: list[dict] | None = None) -> IntentResult:
        history_text = ""
        if chat_history:
            history_text = "\n".join(f"{m['role']}: {m['content']}" for m in chat_history[-5:])

        prompt = f"""Classify the user's intent and extract entities from their message.

Chat history:
{history_text}

User message: {message}

Respond with JSON:
{{
    "intent": "sql_query" | "dashboard_request" | "follow_up" | "clarification" | "general_question",
    "entities": {{
        "tables": ["table names mentioned or implied"],
        "metrics": ["metrics or KPIs mentioned"],
        "filters": ["filter conditions"],
        "time_range": "time period if mentioned"
    }},
    "confidence": 0.0 to 1.0,
    "rewritten_query": "optimized version of the query for schema search"
}}

JSON response:"""

        try:
            result = await self._llm.generate_json(prompt)
            intent_str = result.get("intent", "general_question")
            try:
                intent_type = IntentType(intent_str)
            except ValueError:
                intent_type = IntentType.GENERAL_QUESTION

            return IntentResult(
                intent_type=intent_type,
                entities=result.get("entities", {}),
                confidence=float(result.get("confidence", 0.5)),
                rewritten_query=result.get("rewritten_query", message),
            )
        except Exception as e:
            logger.warning("intent_classification_failed", error=str(e))
            return IntentResult(
                intent_type=IntentType.SQL_QUERY,
                entities={},
                confidence=0.3,
                rewritten_query=message,
            )
