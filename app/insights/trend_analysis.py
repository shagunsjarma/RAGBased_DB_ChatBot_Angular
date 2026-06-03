"""Trend analysis for numeric time-series data."""

from __future__ import annotations

import numpy as np


class TrendAnalysis:
    def analyze(self, data: list[dict], columns: list[str]) -> list[str]:
        trends = []
        for col in columns:
            values = [float(r[col]) for r in data if r.get(col) is not None
                      and self._is_numeric(r[col])]
            if len(values) < 3:
                continue
            direction, slope = self._linear_trend(values)
            growth = self._growth_rate(values)
            trends.append(
                f"{col}: {direction} trend (slope={slope:+.3f}), "
                f"overall growth {growth:+.1f}%"
            )
        return trends

    def _linear_trend(self, values: list[float]) -> tuple[str, float]:
        x = np.arange(len(values), dtype=float)
        coeffs = np.polyfit(x, values, 1)
        slope = coeffs[0]
        if slope > 0.01:
            return "increasing", round(slope, 4)
        elif slope < -0.01:
            return "decreasing", round(slope, 4)
        return "stable", round(slope, 4)

    def _growth_rate(self, values: list[float]) -> float:
        if not values or values[0] == 0:
            return 0.0
        return round(((values[-1] - values[0]) / abs(values[0])) * 100, 1)

    @staticmethod
    def _is_numeric(v) -> bool:
        try:
            float(v)
            return True
        except (ValueError, TypeError):
            return False
