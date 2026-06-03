"""Prompt template rendering and token counting helpers."""

from __future__ import annotations

from typing import Any

import tiktoken


def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
    """Estimate token count in a text block using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Fallback to cl100k_base
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def render_prompt(template: str, **kwargs: Any) -> str:
    """Render a prompt template with variables."""
    return template.format(**kwargs)


def truncate_context_to_limit(
    context_chunks: list[str],
    max_tokens: int = 4000,
    model_name: str = "gpt-3.5-turbo"
) -> list[str]:
    """Truncate context chunks list so total token count is within limits."""
    retained = []
    total_tokens = 0
    for chunk in context_chunks:
        chunk_tokens = count_tokens(chunk, model_name)
        if total_tokens + chunk_tokens > max_tokens:
            break
        retained.append(chunk)
        total_tokens += chunk_tokens
    return retained
