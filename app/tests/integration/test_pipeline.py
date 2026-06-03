"""Integration tests for the orchestration agent pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.orchestration_agent import OrchestrationAgent
from app.core.constants import IntentType
from app.agents.intent_agent import IntentResult
from app.schemas.sql_schema import SQLGenerationResult, SQLValidationResult, QueryExecutionResult


@pytest.mark.asyncio
async def test_orchestrator_pipeline_success() -> None:
    # 1. Setup Mocks
    intent_mock = AsyncMock()
    intent_mock.classify_intent.return_value = IntentResult(
        intent_type=IntentType.SQL_QUERY,
        confidence=0.9,
    )

    retrieval_mock = AsyncMock()
    retrieval_mock.retrieve_context.return_value = "Table users..."

    sql_gen_mock = AsyncMock()
    sql_gen_mock.generate_sql.return_value = SQLGenerationResult(
        sql_query="SELECT * FROM users",
        confidence=0.95,
        explanation="Explain",
    )

    sql_val_mock = AsyncMock()
    sql_val_mock.validate.return_value = SQLValidationResult(
        is_valid=True,
        sanitized_sql="SELECT * FROM users",
    )

    viz_mock = AsyncMock()
    viz_mock.select_visualizations.return_value = [{"chart_type": "bar", "title": "Chart"}]

    insight_mock = AsyncMock()
    insight_mock.generate_insights.return_value = MagicMock()

    summarization_mock = AsyncMock()
    summarization_mock.summarize_response.return_value = "Response content summary"
    summarization_mock.generate_follow_ups.return_value = ["How about Z?", "Show more details"]

    sql_svc_mock = AsyncMock()
    sql_svc_mock.execute_query.return_value = QueryExecutionResult(
        columns=["id", "name"],
        rows=[{"id": 1, "name": "Alice"}],
        row_count=1,
        execution_time_ms=5.0,
    )

    cache_mock = AsyncMock()
    cache_mock.get_cached_result.return_value = None

    orchestrator = OrchestrationAgent(
        intent_agent=intent_mock,
        retrieval_agent=retrieval_mock,
        sql_generation_agent=sql_gen_mock,
        sql_validation_agent=sql_val_mock,
        visualization_agent=viz_mock,
        insight_agent=insight_mock,
        summarization_agent=summarization_mock,
        sql_service=sql_svc_mock,
        cache_service=cache_mock,
    )

    # 2. Execute
    response = await orchestrator.process_message("List all users", user_id=1, conversation_id=100)

    # 3. Verify
    assert response.message == "Response content summary"
    assert response.sql_query == "SELECT * FROM users"
    assert response.conversation_id == 100
    assert len(response.query_results) == 1
    assert response.visualizations[0].chart_type == "bar"
    assert response.follow_up_suggestions == ["How about Z?", "Show more details"]

    intent_mock.classify_intent.assert_called_once()
    retrieval_mock.retrieve_context.assert_called_once()
    sql_gen_mock.generate_sql.assert_called_once()
    sql_val_mock.validate.assert_called_once()
    sql_svc_mock.execute_query.assert_called_once()
