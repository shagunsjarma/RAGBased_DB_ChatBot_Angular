"""Simple exponential smoothing forecasting."""

from __future__ import annotations

import math


class Forecasting:
    def forecast(self, data: list[dict], time_col: str, value_col: str,
                  periods: int = 5) -> dict:
        values = [float(r[value_col]) for r in data if r.get(value_col) is not None
                  and self._is_numeric(r[value_col])]
        if len(values) < 3:
            return {"historical": values, "forecast": [], "confidence_upper": [], "confidence_lower": []}

        forecasted = self._exponential_smoothing(values, alpha=0.3)
        # Extend forecast
        last = forecasted[-1]
        trend = (values[-1] - values[0]) / len(values) if len(values) > 1 else 0
        future = [last + trend * (i + 1) for i in range(periods)]

        std = math.sqrt(sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values)) if values else 1
        upper, lower = self._calculate_confidence(future, std)

        return {
            "historical": values, "forecast": [round(v, 2) for v in future],
            "confidence_upper": upper, "confidence_lower": lower,
        }

    def _exponential_smoothing(self, values: list[float], alpha: float = 0.3) -> list[float]:
        result = [values[0]]
        for v in values[1:]:
            result.append(alpha * v + (1 - alpha) * result[-1])
        return result

    def _calculate_confidence(self, forecast: list[float], std: float) -> tuple[list[float], list[float]]:
        upper = [round(f + 1.96 * std * (1 + 0.1 * i), 2) for i, f in enumerate(forecast)]
        lower = [round(f - 1.96 * std * (1 + 0.1 * i), 2) for i, f in enumerate(forecast)]
        return upper, lower

    @staticmethod
    def _is_numeric(v) -> bool:
        try:
            float(v)
            return True
        except (ValueError, TypeError):
            return False
