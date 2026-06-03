"""Input and parameter validation helpers."""

from __future__ import annotations

import re


def is_valid_email(email: str) -> bool:
    """Check if the provided email string matches a generic email format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def sanitize_identifier(name: str) -> str:
    """Sanitize database identifiers (like table or column names) to avoid injection."""
    # Allow alphanumeric characters and underscores
    return re.sub(r"[^\w]", "", name)


def is_safe_identifier(name: str) -> bool:
    """Verify if a database identifier (table/column name) is alphanumeric + underscore."""
    if not name:
        return False
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))
