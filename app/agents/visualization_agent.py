"""Visualization agent – selects chart types and generates configs."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.prompts.chart_prompt import CHART_SELECTION_PROMPT
from app.core.logger import get_logger

logger = get_logger(__name__)


class VisualizationAgent:
    """Analyzes query results and generates visualization configurations."""

    def __init__(self, llm_service) -> None:
        self._llm = llm_service

    async def select_visualizations(self, query: str, columns: list[str],
                                     data_sample: list[dict], row_count: int) -> list[dict[str, Any]]:
        data_types = self._detect_column_types(columns, data_sample)
        prompt = CHART_SELECTION_PROMPT.format(
            columns=columns, data_types=json.dumps(data_types),
            row_count=row_count, sample_data=json.dumps(data_sample[:3], default=str),
        )
        try:
            result = await self._llm.generate_json(prompt)
            if isinstance(result, list):
                return result[:3]
            return [result]
        except Exception as e:
            logger.warning("llm_chart_selection_failed", error=str(e))
            # Fallback to rule-based
            chart_types = self._rule_based_selection(data_types, row_count)
            fallback = []
            for ct in chart_types:
                numeric_cols = [c for c, t in data_types.items() if t == "numeric"]
                cat_cols = [c for c, t in data_types.items() if t in ("categorical", "temporal")]
                fallback.append({
                    "chart_type": ct,
                    "x_column": cat_cols[0] if cat_cols else columns[0],
                    "y_column": numeric_cols[0] if numeric_cols else columns[-1],
                    "title": f"{ct.title()} Chart",
                })
            return fallback

    def _detect_column_types(self, columns: list[str], data_sample: list[dict]) -> dict[str, str]:
        types = {}
        for col in columns:
            values = [row.get(col) for row in data_sample if row.get(col) is not None]
            if not values:
                types[col] = "text"
                continue
            sample = values[0]
            if isinstance(sample, (int, float)):
                types[col] = "numeric"
            elif isinstance(sample, datetime):
                types[col] = "temporal"
            elif isinstance(sample, str):
                try:
                    float(sample)
                    types[col] = "numeric"
                except (ValueError, TypeError):
                    if any(kw in col.lower() for kw in ("date", "time", "year", "month")):
                        types[col] = "temporal"
                    else:
                        types[col] = "categorical"
            else:
                types[col] = "text"
        return types

    def _rule_based_selection(self, column_types: dict[str, str], row_count: int) -> list[str]:
        numeric = [c for c, t in column_types.items() if t == "numeric"]
        categorical = [c for c, t in column_types.items() if t == "categorical"]
        temporal = [c for c, t in column_types.items() if t == "temporal"]

        charts = []
        if temporal and numeric:
            charts.append("line")
        if categorical and numeric:
            charts.append("bar")
            if len(set(categorical)) == 1 and row_count <= 8:
                charts.append("pie")
        if len(numeric) >= 2:
            charts.append("scatter")
        if not charts:
            charts.append("bar")
        return charts[:3]
