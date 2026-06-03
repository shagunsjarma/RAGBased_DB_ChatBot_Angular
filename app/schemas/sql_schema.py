"""SQL generation and execution schemas."""

from __future__ import annotations

from pydantic import BaseModel


class SQLGenerationResult(BaseModel):
    sql_query: str
    confidence: float = 0.0
    explanation: str = ""
    tables_used: list[str] = []


class SQLValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    sanitized_sql: str | None = None


class QueryExecutionResult(BaseModel):
    columns: list[str]
    rows: list[dict]
    row_count: int
    execution_time_ms: float
    truncated: bool = False


class SQLExplainRequest(BaseModel):
    sql_query: str


class SQLExplainResponse(BaseModel):
    explanation: str
    execution_plan: str | None = None
