"""Rule-based chart type selector."""

from __future__ import annotations

from datetime import datetime


class ChartSelector:
    def select_chart_types(self, columns: list[str], data_types: dict[str, str],
                            row_count: int, data_sample: list[dict]) -> list[str]:
        numeric = [c for c, t in data_types.items() if t == "numeric"]
        categorical = [c for c, t in data_types.items() if t == "categorical"]
        temporal = [c for c, t in data_types.items() if t == "temporal"]

        charts: list[str] = []

        if temporal and numeric:
            charts.append("line")
        if categorical and numeric:
            charts.append("bar")
            if row_count <= 8:
                charts.append("pie")
        if len(numeric) >= 2 and not temporal:
            charts.append("scatter")
        if len(numeric) == 1 and not categorical and not temporal:
            charts.append("histogram")
        if len(categorical) >= 2 and numeric:
            charts.append("heatmap")
        if row_count == 1 and numeric:
            charts.insert(0, "kpi")

        return charts[:3] if charts else ["bar"]

    def _is_temporal(self, column: str, data_sample: list[dict]) -> bool:
        for row in data_sample:
            v = row.get(column)
            if isinstance(v, datetime):
                return True
            if isinstance(v, str):
                for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"):
                    try:
                        datetime.strptime(v, fmt)
                        return True
                    except ValueError:
                        continue
        return any(kw in column.lower() for kw in ("date", "time", "year", "month", "day"))

    def _is_numeric(self, column: str, data_sample: list[dict]) -> bool:
        for row in data_sample:
            v = row.get(column)
            if v is None:
                continue
            if isinstance(v, (int, float)):
                return True
            try:
                float(str(v))
                return True
            except (ValueError, TypeError):
                return False
        return False

    def _analyze_cardinality(self, column: str, data: list[dict]) -> int:
        return len({row.get(column) for row in data if row.get(column) is not None})
