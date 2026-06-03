"""Anomaly detection using Z-score and IQR methods."""

from __future__ import annotations

import math


class AnomalyDetection:
    def detect(self, data: list[dict], columns: list[str]) -> list[str]:
        anomalies = []
        for col in columns:
            values = [float(r[col]) for r in data if r.get(col) is not None
                      and self._is_numeric(r[col])]
            if len(values) < 5:
                continue
            z_anoms = self._zscore_anomalies(values)
            iqr_anoms = self._iqr_anomalies(values)
            all_indices = {idx for idx, _ in z_anoms} | {idx for idx, _ in iqr_anoms}
            if all_indices:
                anomalies.append(
                    f"{col}: {len(all_indices)} anomalous values detected "
                    f"(indices: {sorted(all_indices)[:5]})"
                )
        return anomalies

    def _zscore_anomalies(self, values: list[float], threshold: float = 2.5) -> list[tuple[int, float]]:
        n = len(values)
        mean = sum(values) / n
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) or 1
        return [(i, v) for i, v in enumerate(values) if abs((v - mean) / std) > threshold]

    def _iqr_anomalies(self, values: list[float]) -> list[tuple[int, float]]:
        s = sorted(values)
        n = len(s)
        q1, q3 = s[n // 4], s[3 * n // 4]
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        return [(i, v) for i, v in enumerate(values) if v < lower or v > upper]

    @staticmethod
    def _is_numeric(v) -> bool:
        try:
            float(v)
            return True
        except (ValueError, TypeError):
            return False
