"""KPI card generator."""

from __future__ import annotations


class KPIGenerator:
    def generate_kpis(self, data: list[dict], columns: list[str]) -> list[dict]:
        kpis = []
        for col in columns:
            values = []
            for row in data:
                v = row.get(col)
                if v is not None:
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        continue
            if not values:
                continue

            current = values[-1]
            mean_val = sum(values) / len(values)
            direction, trend_pct = self._calculate_trend(values)

            kpis.append({
                "title": self._format_title(col),
                "value": current,
                "formatted_value": self._format_value(current, col),
                "trend_direction": direction,
                "trend_value": trend_pct,
                "sparkline_data": self._generate_sparkline(values),
            })
        return kpis

    def _format_value(self, value: float, column_name: str) -> str:
        name_lower = column_name.lower()
        if any(kw in name_lower for kw in ("amount", "price", "revenue", "cost", "sales", "total")):
            return f"${value:,.2f}"
        if any(kw in name_lower for kw in ("rate", "percent", "ratio")):
            return f"{value:.1f}%"
        if value == int(value):
            return f"{int(value):,}"
        return f"{value:,.2f}"

    def _format_title(self, col: str) -> str:
        return col.replace("_", " ").title()

    def _calculate_trend(self, values: list[float]) -> tuple[str, float]:
        if len(values) < 2:
            return "neutral", 0.0
        last, prev = values[-1], sum(values[:-1]) / len(values[:-1])
        if prev == 0:
            return "neutral", 0.0
        pct = round(((last - prev) / abs(prev)) * 100, 1)
        direction = "up" if pct > 1 else "down" if pct < -1 else "neutral"
        return direction, abs(pct)

    def _generate_sparkline(self, values: list[float]) -> list[float]:
        if not values:
            return []
        mn, mx = min(values), max(values)
        rng = mx - mn if mx != mn else 1
        return [round((v - mn) / rng, 2) for v in values[-20:]]
