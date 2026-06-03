"""Chart styling constants, themes, and configuration helpers."""

from __future__ import annotations

# Consistent premium dark theme colors
THEME_COLORS = [
    "#6366f1",  # Indigo
    "#14b8a6",  # Teal
    "#f59e0b",  # Amber
    "#ef4444",  # Red
    "#8b5cf6",  # Purple
    "#ec4899",  # Pink
    "#3b82f6",  # Blue
    "#10b981",  # Emerald
]

DARK_LAYOUT_TEMPLATE = {
    "paper_bgcolor": "#0f172a",  # slate-900
    "plot_bgcolor": "#1e293b",   # slate-800
    "font": {
        "color": "#f8fafc",      # slate-50
        "family": "Inter, Roboto, sans-serif"
    },
    "xaxis": {
        "gridcolor": "#334155",  # slate-700
        "linecolor": "#475569",  # slate-600
        "zerolinecolor": "#475569"
    },
    "yaxis": {
        "gridcolor": "#334155",
        "linecolor": "#475569",
        "zerolinecolor": "#475569"
    },
    "margin": {"t": 40, "b": 40, "l": 40, "r": 40},
}
