"""Insight service – trend, anomaly, and forecast analysis."""

from __future__ import annotations

from app.insights.trend_analysis import TrendAnalysis
from app.insights.anomaly_detection import AnomalyDetection
from app.insights.forecasting import Forecasting


class InsightService:
    def __init__(self) -> None:
        self._trend = TrendAnalysis()
        self._anomaly = AnomalyDetection()
        self._forecast = Forecasting()

    def analyze_trends(self, data: list[dict], columns: list[str]) -> list[str]:
        return self._trend.analyze(data, columns)

    def detect_anomalies(self, data: list[dict], columns: list[str]) -> list[str]:
        return self._anomaly.detect(data, columns)

    def generate_forecast(self, data: list[dict], time_col: str,
                           value_col: str, periods: int = 5) -> dict:
        return self._forecast.forecast(data, time_col, value_col, periods)
