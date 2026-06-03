"""System-wide constants and enumerations."""

from __future__ import annotations

from enum import Enum

# ── Token / LLM limits ───────────────────────────────────────────────
MAX_TOKEN_LIMIT: int = 8192
DEFAULT_CONTEXT_WINDOW: int = 4000

# ── Pagination ───────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# ── Supported chart types ────────────────────────────────────────────
SUPPORTED_CHART_TYPES: list[str] = [
    "bar", "line", "scatter", "pie", "histogram",
    "heatmap", "treemap", "funnel", "kpi",
]

# ── SQL safety ───────────────────────────────────────────────────────
SQL_BLACKLIST_KEYWORDS: list[str] = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE",
    "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC",
]
SQL_DANGEROUS_PATTERNS: list[str] = [
    "SLEEP", "BENCHMARK", "LOAD_FILE", "INTO OUTFILE",
    "INTO DUMPFILE", "INFORMATION_SCHEMA",
]
MAX_SQL_EXECUTION_TIME: int = 30  # seconds
MAX_RESULT_ROWS: int = 10_000

# ── Cache ────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS: int = 300

# ── RAG ──────────────────────────────────────────────────────────────
EMBEDDING_BATCH_SIZE: int = 100
TOP_K_RETRIEVAL: int = 10
RERANKER_TOP_K: int = 5


# ── Enums ────────────────────────────────────────────────────────────
class IntentType(str, Enum):
    SQL_QUERY = "sql_query"
    DASHBOARD_REQUEST = "dashboard_request"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    GENERAL_QUESTION = "general_question"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QueryStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    VALIDATION_FAILED = "validation_failed"
