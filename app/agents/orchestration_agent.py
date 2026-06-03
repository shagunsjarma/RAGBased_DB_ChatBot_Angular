"""Orchestration agent – central pipeline coordinator."""

from __future__ import annotations

import json
import time
from typing import Any

from app.agents.intent_agent import IntentAgent, IntentResult
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.sql_generation_agent import SQLGenerationAgent
from app.agents.sql_validation_agent import SQLValidationAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.insight_agent import InsightAgent
from app.agents.summarization_agent import SummarizationAgent
from app.core.constants import IntentType
from app.schemas.chat_schema import ChatResponse, VisualizationData
from app.core.logger import get_logger

logger = get_logger(__name__)


class OrchestrationAgent:
    """Routes user messages through the full agent pipeline and returns
    a structured ``ChatResponse``."""

    def __init__(
        self,
        intent_agent: IntentAgent,
        retrieval_agent: RetrievalAgent,
        sql_generation_agent: SQLGenerationAgent,
        sql_validation_agent: SQLValidationAgent,
        visualization_agent: VisualizationAgent,
        insight_agent: InsightAgent,
        summarization_agent: SummarizationAgent,
        sql_service,
        cache_service,
    ) -> None:
        self._intent = intent_agent
        self._retrieval = retrieval_agent
        self._sql_gen = sql_generation_agent
        self._sql_val = sql_validation_agent
        self._viz = visualization_agent
        self._insight = insight_agent
        self._summary = summarization_agent
        self._sql_svc = sql_service
        self._cache_svc = cache_service

    async def process_message(
        self,
        user_message: str,
        user_id: int,
        conversation_id: int = 0,
        chat_history: list[dict[str, str]] | None = None,
    ) -> ChatResponse:
        t0 = time.perf_counter()

        # ── 1. Classify intent ───────────────────────────────────────
        intent = await self._intent.classify_intent(user_message, chat_history)
        logger.info("intent_classified", intent=intent.intent_type.value,
                     confidence=intent.confidence)

        # ── 2. Handle non-SQL intents ────────────────────────────────
        if intent.intent_type in (IntentType.GENERAL_QUESTION, IntentType.CLARIFICATION):
            reply = await self._summary.summarize_response(
                sql="", results_summary=user_message,
                insights={}, chart_descriptions=[],
            )
            return ChatResponse(
                message=reply, conversation_id=conversation_id,
            )

        # ── 3. Check cache ───────────────────────────────────────────
        if self._cache_svc:
            cached = await self._cache_svc.get_cached_result(user_message)
            if cached:
                logger.info("cache_hit", query=user_message[:80])
                return ChatResponse(**cached, conversation_id=conversation_id)

        # ── 4. Retrieve schema context ───────────────────────────────
        schema_context = await self._retrieval.retrieve_context(intent, chat_history)

        # ── 5. Generate SQL ──────────────────────────────────────────
        sql_result = await self._sql_gen.generate_sql(
            user_message, schema_context, chat_history,
        )
        if not sql_result.sql_query:
            return ChatResponse(
                message="I couldn't generate a SQL query for your request. Could you rephrase?",
                conversation_id=conversation_id,
            )

        # ── 6. Validate SQL ──────────────────────────────────────────
        validation = await self._sql_val.validate(sql_result.sql_query)
        sql_to_run = validation.sanitized_sql or sql_result.sql_query

        if not validation.is_valid:
            error_detail = "; ".join(validation.errors)
            return ChatResponse(
                message=f"Generated SQL failed validation: {error_detail}",
                conversation_id=conversation_id,
                sql_query=sql_result.sql_query,
            )

        # ── 7. Execute SQL ───────────────────────────────────────────
        try:
            exec_result = await self._sql_svc.execute_query(sql_to_run)
        except Exception as exc:
            logger.error("sql_execution_failed", error=str(exc))
            return ChatResponse(
                message=f"SQL execution failed: {exc}",
                conversation_id=conversation_id,
                sql_query=sql_to_run,
            )

        rows = exec_result.rows
        columns = exec_result.columns

        # ── 8. Generate visualizations ───────────────────────────────
        visualizations: list[VisualizationData] = []
        if rows:
            try:
                viz_configs = await self._viz.select_visualizations(
                    user_message, columns, rows[:100], exec_result.row_count,
                )
                visualizations = [
                    VisualizationData(
                        chart_type=v.get("chart_type", "bar"),
                        chart_config=v,
                        title=v.get("title"),
                    )
                    for v in viz_configs
                ]
            except Exception as exc:
                logger.warning("visualization_failed", error=str(exc))

        # ── 9. Generate insights ─────────────────────────────────────
        insights = None
        if rows:
            try:
                insights = await self._insight.generate_insights(
                    user_message, columns, rows, sql_to_run,
                )
            except Exception as exc:
                logger.warning("insight_generation_failed", error=str(exc))

        # ── 10. Summarize ────────────────────────────────────────────
        results_summary = (
            f"Query returned {exec_result.row_count} rows with columns: "
            f"{', '.join(columns)}."
        )
        chart_descs = [v.title or v.chart_type for v in visualizations]

        message = await self._summary.summarize_response(
            sql=sql_to_run,
            results_summary=results_summary,
            insights=insights.model_dump() if insights else {},
            chart_descriptions=chart_descs,
        )

        # ── 11. Follow-up suggestions ────────────────────────────────
        follow_ups = await self._summary.generate_follow_ups(
            user_message, results_summary, chat_history,
        )

        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        logger.info("pipeline_complete", duration_ms=elapsed,
                     rows=exec_result.row_count, charts=len(visualizations))

        response = ChatResponse(
            message=message,
            conversation_id=conversation_id,
            sql_query=sql_to_run,
            query_results=rows[:500],          # cap payload
            visualizations=visualizations or None,
            insights=insights,
            follow_up_suggestions=follow_ups or None,
        )

        # ── 12. Cache ────────────────────────────────────────────────
        if self._cache_svc:
            try:
                await self._cache_svc.cache_result(
                    user_message, response.model_dump(exclude={"conversation_id"}),
                )
            except Exception:
                pass

        return response
