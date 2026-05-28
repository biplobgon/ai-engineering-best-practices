"""
OpenTelemetry instrumentation and cost metrics.

Design principles:
- Every LLM call emits an OTel span
- Spans include: tokens_in, tokens_out, usd_cost, latency_ms, model, cached
- Metrics: counters for tokens + cost, histograms for latency
- Vendor-neutral (works with Jaeger, Datadog, New Relic, etc.)
"""

from typing import Callable, TypeVar, Any
from functools import wraps
import time

F = TypeVar("F")


def traced(span_name: str) -> Callable[[Callable[..., F]], Callable[..., F]]:
    """
    Decorator: emit OTel span with token/cost attributes.

    Args:
        span_name: Name of span (e.g., "llm.chat", "vector_db.search")

    Returns:
        Decorated function that emits OTel spans

    Usage:
        >>> @traced("my_task")
        ... async def my_function(...):
        ...     ...
        ...
        >>> # Span will include: tokens_in, tokens_out, usd_cost, latency_ms
    """
    raise NotImplementedError


class Meters:
    """Prometheus-style metrics."""

    @staticmethod
    def increment_tokens_in(tokens: int, model: str) -> None:
        """Increment input token counter."""
        raise NotImplementedError

    @staticmethod
    def increment_tokens_out(tokens: int, model: str) -> None:
        """Increment output token counter."""
        raise NotImplementedError

    @staticmethod
    def increment_usd_cost(cost: float, model: str) -> None:
        """Increment cost counter."""
        raise NotImplementedError

    @staticmethod
    def record_latency_ms(latency: float, operation: str) -> None:
        """Record operation latency (histogram)."""
        raise NotImplementedError

    @staticmethod
    def increment_cache_hits(cache_type: str) -> None:
        """Increment cache hit counter (exact or semantic)."""
        raise NotImplementedError


meters: Meters = Meters()
"""Global metrics instance."""
