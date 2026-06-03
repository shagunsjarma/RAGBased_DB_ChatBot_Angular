"""SQL utility helpers."""

from __future__ import annotations

import re
import sqlparse


def clean_sql(sql: str) -> str:
    """Strip markdown fences, comments, and normalize whitespace."""
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        sql = "\n".join(lines).strip()
    sql = sqlparse.format(sql, strip_comments=True)
    sql = sql.rstrip(";").strip()
    return sql


def extract_table_names(sql: str) -> list[str]:
    """Extract table names from FROM and JOIN clauses."""
    pattern = r'\b(?:FROM|JOIN)\s+`?(\w+)`?'
    return list(set(re.findall(pattern, sql, re.IGNORECASE)))


def add_limit(sql: str, limit: int = 1000) -> str:
    """Add LIMIT clause if not present."""
    if "LIMIT" not in sql.upper():
        return f"{sql} LIMIT {limit}"
    return sql


def is_select_only(sql: str) -> bool:
    """Check that the SQL is a SELECT statement."""
    normalised = " ".join(sql.upper().split())
    return normalised.startswith("SELECT")
