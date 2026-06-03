"""Plotly chart builder with dark theme."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

COLORS = ["#6366f1", "#14b8a6", "#f59e0b", "#ef4444", "#8b5cf6",
          "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#a855f7"]


class PlotlyBuilder:
    """Builds Plotly figures and returns them as JSON-serializable dicts."""

    def build_chart(self, chart_type: str, data: list[dict], config: dict) -> dict:
        builders = {
            "bar": self._build_bar, "line": self._build_line,
            "scatter": self._build_scatter, "pie": self._build_pie,
            "histogram": self._build_histogram, "heatmap": self._build_heatmap,
            "treemap": self._build_treemap, "funnel": self._build_funnel,
        }
        builder = builders.get(chart_type, self._build_bar)
        fig = builder(data, config)
        fig.update_layout(**self._dark_theme_layout(config.get("title", "Chart")))
        return fig.to_dict()

    def _build_bar(self, data: list[dict], config: dict) -> go.Figure:
        x_col = config.get("x_column", list(data[0].keys())[0] if data else "x")
        y_col = config.get("y_column", list(data[0].keys())[-1] if data else "y")
        x = [row.get(x_col) for row in data]
        y = [row.get(y_col) for row in data]
        fig = go.Figure(go.Bar(x=x, y=y, marker_color=COLORS[0],
                               marker_line_color=COLORS[0], marker_line_width=0))
        return fig

    def _build_line(self, data: list[dict], config: dict) -> go.Figure:
        x_col = config.get("x_column", list(data[0].keys())[0] if data else "x")
        y_col = config.get("y_column", list(data[0].keys())[-1] if data else "y")
        x = [row.get(x_col) for row in data]
        y = [row.get(y_col) for row in data]
        fig = go.Figure(go.Scatter(x=x, y=y, mode="lines+markers",
                                   line=dict(color=COLORS[1], width=2),
                                   marker=dict(size=6)))
        return fig

    def _build_scatter(self, data: list[dict], config: dict) -> go.Figure:
        x_col = config.get("x_column", list(data[0].keys())[0] if data else "x")
        y_col = config.get("y_column", list(data[0].keys())[-1] if data else "y")
        x = [row.get(x_col) for row in data]
        y = [row.get(y_col) for row in data]
        fig = go.Figure(go.Scatter(x=x, y=y, mode="markers",
                                   marker=dict(color=COLORS[4], size=8, opacity=0.7)))
        return fig

    def _build_pie(self, data: list[dict], config: dict) -> go.Figure:
        label_col = config.get("x_column", list(data[0].keys())[0] if data else "label")
        value_col = config.get("y_column", list(data[0].keys())[-1] if data else "value")
        labels = [row.get(label_col) for row in data]
        values = [row.get(value_col) for row in data]
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.4,
                               marker_colors=COLORS[:len(labels)]))
        return fig

    def _build_histogram(self, data: list[dict], config: dict) -> go.Figure:
        col = config.get("x_column", list(data[0].keys())[0] if data else "x")
        values = [row.get(col) for row in data if row.get(col) is not None]
        fig = go.Figure(go.Histogram(x=values, marker_color=COLORS[2]))
        return fig

    def _build_heatmap(self, data: list[dict], config: dict) -> go.Figure:
        keys = list(data[0].keys()) if data else []
        z = [[row.get(k) for k in keys] for row in data[:50]]
        fig = go.Figure(go.Heatmap(z=z, x=keys, colorscale="Viridis"))
        return fig

    def _build_treemap(self, data: list[dict], config: dict) -> go.Figure:
        label_col = config.get("x_column", list(data[0].keys())[0] if data else "label")
        value_col = config.get("y_column", list(data[0].keys())[-1] if data else "value")
        labels = [str(row.get(label_col, "")) for row in data]
        values = [row.get(value_col, 0) for row in data]
        parents = [""] * len(labels)
        fig = go.Figure(go.Treemap(labels=labels, parents=parents, values=values,
                                   marker_colors=COLORS[:len(labels)]))
        return fig

    def _build_funnel(self, data: list[dict], config: dict) -> go.Figure:
        label_col = config.get("x_column", list(data[0].keys())[0] if data else "stage")
        value_col = config.get("y_column", list(data[0].keys())[-1] if data else "value")
        labels = [row.get(label_col) for row in data]
        values = [row.get(value_col) for row in data]
        fig = go.Figure(go.Funnel(y=labels, x=values, marker_color=COLORS[0]))
        return fig

    def _dark_theme_layout(self, title: str) -> dict[str, Any]:
        return {
            "title": dict(text=title, font=dict(color="#e0e0e0", size=16, family="Inter")),
            "paper_bgcolor": "#16213e",
            "plot_bgcolor": "#1a1a2e",
            "font": dict(color="#e0e0e0", family="Inter"),
            "xaxis": dict(gridcolor="#2a2a4a", zerolinecolor="#2a2a4a"),
            "yaxis": dict(gridcolor="#2a2a4a", zerolinecolor="#2a2a4a"),
            "margin": dict(l=50, r=30, t=50, b=40),
            "legend": dict(bgcolor="rgba(0,0,0,0)"),
        }
