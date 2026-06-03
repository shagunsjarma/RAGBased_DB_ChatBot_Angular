"""Observability utility for tracking LLM token consumption and costs."""

from __future__ import annotations

from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)

# Costs per 1M tokens (Gemini 1.5 Flash typical pricing as placeholder)
COSTS = {
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
}


class TokenTracker:
    """Utility to track LLM token counts and calculate estimated costs."""

    def __init__(self) -> None:
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_estimated_cost = 0.0

    def track_call(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        user_id: int | None = None,
        context: str | None = None,
    ) -> float:
        """Track an LLM call's token usage and return estimated cost in USD."""
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens

        # Estimate cost
        rates = COSTS.get(model_name, COSTS["gemini-1.5-flash"])
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]
        est_cost = input_cost + output_cost

        self._total_estimated_cost += est_cost

        logger.info(
            "llm_token_usage",
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=f"${est_cost:.6f}",
            user_id=user_id,
            context=context,
        )

        return est_cost

    @property
    def total_usage(self) -> dict[str, Any]:
        """Get cumulative token usage stats."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_estimated_cost_usd": round(self._total_estimated_cost, 6),
        }
