"""Prometheus metrics definitions."""

from __future__ import annotations

import time

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_LATENCY = Histogram("request_latency_seconds", "Request latency", ["method", "endpoint", "status"])
REQUEST_COUNT = Counter("request_count_total", "Total requests", ["method", "endpoint", "status"])
LLM_CALL_DURATION = Histogram("llm_call_duration_seconds", "LLM API call duration", ["model", "operation"])
LLM_TOKEN_USAGE = Counter("llm_token_usage_total", "LLM tokens used", ["model", "type"])
SQL_EXECUTION_TIME = Histogram("sql_execution_time_seconds", "SQL query execution time")
CACHE_HITS = Counter("cache_hits_total", "Cache hits")
CACHE_MISSES = Counter("cache_misses_total", "Cache misses")
ACTIVE_CONNECTIONS = Gauge("active_db_connections", "Active database connections")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        endpoint = request.url.path
        REQUEST_LATENCY.labels(request.method, endpoint, response.status_code).observe(duration)
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        return response


def get_metrics() -> bytes:
    return generate_latest()
