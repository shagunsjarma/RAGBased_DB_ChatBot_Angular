"""DataFrame and tabular data profile/conversion helpers."""

from __future__ import annotations

import math
from typing import Any


def infer_data_types(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, str]:
    """Infer the general data types of columns in a list of row dicts.

    Types: 'date', 'number', 'string', 'boolean'
    """
    types = {}
    if not rows:
        return {col: "string" for col in columns}

    for col in columns:
        # Sample non-None values from the first few rows
        sample_values = []
        for r in rows[:10]:
            val = r.get(col)
            if val is not None:
                sample_values.append(val)

        if not sample_values:
            types[col] = "string"
            continue

        # Check types
        is_num = all(isinstance(v, (int, float)) for v in sample_values)
        is_bool = all(isinstance(v, bool) for v in sample_values)

        # Check for dates
        is_date = False
        if all(isinstance(v, str) for v in sample_values):
            # Check basic date formats: YYYY-MM-DD or similar
            date_patterns = [
                r"^\d{4}-\d{2}-\d{2}$",
                r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}",
            ]
            import re
            is_date = all(
                any(re.match(pat, v) for pat in date_patterns)
                for v in sample_values
            )

        if is_num:
            types[col] = "number"
        elif is_bool:
            types[col] = "boolean"
        elif is_date:
            types[col] = "date"
        else:
            types[col] = "string"

    return types


def clean_row_values(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sanitize float values like NaN/Inf to None/null for clean JSON serialization."""
    cleaned = []
    for row in rows:
        r_clean = {}
        for k, v in row.items():
            if isinstance(v, float):
                if math.isnan(v) or math.isinf(v):
                    r_clean[k] = None
                else:
                    r_clean[k] = v
            else:
                r_clean[k] = v
        cleaned.append(r_clean)
    return cleaned
