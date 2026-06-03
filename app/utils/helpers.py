"""Utility helper functions for general app use."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any


def generate_uuid() -> str:
    """Generate a clean string UUID4."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Get the current datetime in UTC."""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime to string."""
    return dt.strftime(fmt)


def clean_string(text: str) -> str:
    """Remove special characters and multiple spaces."""
    text = re.sub(r"[^\w\s\-\.\,\:\?]", "", text)
    return " ".join(text.split())


def extract_json_from_text(text: str) -> dict[str, Any] | list[Any] | None:
    """Extract a JSON structure from a text string that may contain markdown blocks."""
    text = text.strip()
    if not text:
        return None

    # Try straight JSON load first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Search for json code block markdown
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Look for opening and closing brackets/braces
    try:
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            return json.loads(text[brace_start:brace_end + 1])
    except json.JSONDecodeError:
        pass

    try:
        bracket_start = text.find("[")
        bracket_end = text.rfind("]")
        if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
            return json.loads(text[bracket_start:bracket_end + 1])
    except json.JSONDecodeError:
        pass

    return None
