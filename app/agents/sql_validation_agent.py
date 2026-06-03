"""SQL validation agent – safety and correctness checks."""

from __future__ import annotations

import re

import sqlparse

from app.core.constants import SQL_BLACKLIST_KEYWORDS, SQL_DANGEROUS_PATTERNS
from app.schemas.sql_schema import SQLValidationResult
from app.core.logger import get_logger

logger = get_logger(__name__)


class SQLValidationAgent:
    """Validates and sanitizes SQL queries for safety and correctness."""

    def __init__(self, read_only: bool = True) -> None:
        self._read_only = read_only

    async def validate(self, sql: str, available_tables: list[str] | None = None,
                       available_columns: dict[str, list[str]] | None = None) -> SQLValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not sql or not sql.strip():
            return SQLValidationResult(is_valid=False, errors=["Empty SQL query"])

        # 1. Parse SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                errors.append("Failed to parse SQL")
        except Exception as e:
            errors.append(f"SQL syntax error: {e}")

        # 2. Check for DML/DDL (read-only mode)
        if self._read_only:
            sql_upper = sql.upper()
            for keyword in SQL_BLACKLIST_KEYWORDS:
                pattern = r'\b' + keyword + r'\b'
                if re.search(pattern, sql_upper):
                    errors.append(f"Forbidden keyword detected: {keyword}. Only SELECT queries are allowed.")

        # 3. Check for dangerous patterns
        sql_upper = sql.upper()
        for pattern in SQL_DANGEROUS_PATTERNS:
            if pattern in sql_upper:
                errors.append(f"Dangerous pattern detected: {pattern}")

        # 4. Check for SQL injection patterns
        if re.search(r';\s*(SELECT|INSERT|UPDATE|DELETE|DROP)', sql, re.IGNORECASE):
            errors.append("Potential SQL injection: stacked queries detected")
        if re.search(r'--\s', sql) or '/*' in sql:
            warnings.append("SQL comments detected and will be removed")

        # 5. Verify table names
        if available_tables:
            tables_in_sql = self._extract_tables(sql)
            for table in tables_in_sql:
                if table.lower() not in [t.lower() for t in available_tables]:
                    errors.append(f"Table '{table}' does not exist in the database")

        # 6. Warnings
        if re.search(r'SELECT\s+\*', sql, re.IGNORECASE) and 'LIMIT' not in sql.upper():
            warnings.append("SELECT * without LIMIT may return too many rows")

        if 'LIMIT' not in sql.upper():
            warnings.append("Consider adding a LIMIT clause")

        sanitized = self._sanitize_sql(sql) if not errors else None

        return SQLValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_sql=sanitized,
        )

    def _extract_tables(self, sql: str) -> list[str]:
        pattern = r'\b(?:FROM|JOIN)\s+`?(\w+)`?'
        return list(set(re.findall(pattern, sql, re.IGNORECASE)))

    def _sanitize_sql(self, sql: str) -> str:
        """Remove comments, trailing semicolons, normalize whitespace."""
        sql = sqlparse.format(sql, strip_comments=True)
        sql = sql.rstrip(";").strip()
        sql = " ".join(sql.split())
        return sql
