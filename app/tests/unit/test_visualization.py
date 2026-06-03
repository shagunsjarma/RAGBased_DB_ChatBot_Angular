"""Unit tests for the visualization engine."""

from __future__ import annotations

import pytest

from app.visualization.chart_selector import ChartSelector


def test_chart_selector_numeric() -> None:
    selector = ChartSelector()
    columns = ["region", "sales"]
    data_types = {"region": "string", "sales": "number"}
    rows = [
        {"region": "North", "sales": 5000},
        {"region": "South", "sales": 6000},
        {"region": "East", "sales": 4000},
    ]

    charts = selector.select_chart_types(columns, data_types, len(rows), rows)
    
    # Should recommend at least a bar chart for categorical vs numeric
    assert len(charts) >= 1
    assert "bar" in charts
