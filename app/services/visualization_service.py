"""Visualization service – chart generation via Plotly."""

from __future__ import annotations

from app.visualization.plotly_builder import PlotlyBuilder
from app.visualization.kpi_generator import KPIGenerator


class VisualizationService:
    def __init__(self) -> None:
        self._builder = PlotlyBuilder()
        self._kpi_gen = KPIGenerator()

    def generate_chart(self, chart_type: str, data: list[dict], config: dict) -> dict:
        return self._builder.build_chart(chart_type, data, config)

    def generate_kpis(self, data: list[dict], columns: list[str]) -> list[dict]:
        return self._kpi_gen.generate_kpis(data, columns)
