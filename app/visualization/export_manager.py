"""Chart and data export manager."""

from __future__ import annotations

import csv
import io

import plotly.graph_objects as go
import plotly.io as pio


class ExportManager:
    def export_chart_image(self, chart_json: dict, fmt: str = "png",
                            width: int = 1200, height: int = 800) -> bytes:
        fig = go.Figure(chart_json)
        return pio.to_image(fig, format=fmt, width=width, height=height)

    def export_data_csv(self, data: list[dict], columns: list[str]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    def export_data_excel(self, data: list[dict], columns: list[str]) -> bytes:
        import pandas as pd
        df = pd.DataFrame(data, columns=columns)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        return output.getvalue()
