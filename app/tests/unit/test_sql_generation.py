"""Unit tests for the SQL generation agent."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.sql_generation_agent import SQLGenerationAgent


@pytest.mark.asyncio
async def test_sql_generation_success() -> None:
    # Mock LLMService
    llm_mock = AsyncMock()
    llm_mock.generate.return_value = "SELECT * FROM users WHERE is_active = 1"

    agent = SQLGenerationAgent(llm_service=llm_mock)
    
    # Execute
    result = await agent.generate_sql("List all active users", "Schema Context")

    # Verify
    assert result.sql_query == "SELECT * FROM users WHERE is_active = 1"
    assert result.confidence == 0.85
    assert result.explanation == "Generated SQL to answer: List all active users"
    assert result.tables_used == ["users"]
    
    llm_mock.generate.assert_awaited_once()
