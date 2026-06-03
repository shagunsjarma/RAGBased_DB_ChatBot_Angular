"""Structured logging setup (re-exports from core.logger)."""

from app.core.logger import setup_logging, get_logger

__all__ = ["setup_logging", "get_logger"]
