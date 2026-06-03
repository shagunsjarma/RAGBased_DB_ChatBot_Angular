"""Unit tests for the SQL validation agent."""

from __future__ import annotations

import pytest

from app.agents.sql_validation_agent import SQLValidationAgent


@pytest.mark.asyncio
async def test_sql_validation_safe() -> None:
    validator = SQLValidationAgent()
    
    # Secure read-only queries should pass
    res = await validator.validate("SELECT id, name FROM users WHERE id = 12;")
    assert res.is_valid is True
    assert not res.errors


@pytest.mark.asyncio
async def test_sql_validation_unsafe() -> None:
    validator = SQLValidationAgent()
    
    # Dangerous statements should fail
    res_drop = await validator.validate("DROP TABLE users;")
    assert res_drop.is_valid is False
    assert any("DROP" in err for err in res_drop.errors)

    res_delete = await validator.validate("DELETE FROM users;")
    assert res_delete.is_valid is False
    assert any("DELETE" in err for err in res_delete.errors)
