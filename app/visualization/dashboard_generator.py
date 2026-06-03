"""Dashboard layout generator."""

from __future__ import annotations


class DashboardGenerator:
    """Arranges widgets into a responsive 12-column grid layout."""

    _SIZES = {
        "kpi": (3, 2), "bar": (6, 4), "line": (6, 4), "scatter": (6, 4),
        "pie": (4, 4), "histogram": (6, 4), "heatmap": (6, 5),
        "treemap": (6, 5), "funnel": (6, 4), "table": (12, 4),
    }

    def generate_dashboard_layout(self, widgets: list[dict]) -> dict:
        positioned: list[dict] = []
        x, y, row_height = 0, 0, 0

        for widget in widgets:
            chart_type = widget.get("chart_type", "bar")
            w, h = self._calculate_widget_size(chart_type)

            if x + w > 12:
                x = 0
                y += row_height
                row_height = 0

            positioned.append({**widget, "position_x": x, "position_y": y, "width": w, "height": h})
            x += w
            row_height = max(row_height, h)

        return {"widgets": positioned, "grid_cols": 12}

    def _calculate_widget_size(self, chart_type: str) -> tuple[int, int]:
        return self._SIZES.get(chart_type, (6, 4))
