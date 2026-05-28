"""
OpenTelemetry instrumentation and cost metrics.

Design principles:
- Every LLM call emits an OTel span
- Spans include: tokens_in, tokens_out, usd_cost, latency_ms, model, cached
- Metrics: counters for tokens + cost, histograms for latency
- Vendor-neutral (works with Jaeger, Datadog, New Relic, etc.)
"""

import functools
import logging
import time
from typing import Any, Callable, TypeVar

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from core.config import get_settings


logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Initialize tracer
_tracer: trace.Tracer | None = None


def _get_tracer() -> trace.Tracer:
    """Get or initialize tracer."""
    global _tracer
    if _tracer is None:
        settings = get_settings()

        # Only initialize if tracing is enabled
        if not settings.ENABLE_TRACING:
            _tracer = trace.get_tracer(__name__)
            return _tracer

        # Create resource
        resource = Resource.create({"service.name": settings.SERVICE_NAME})

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Add Jaeger exporter
        try:
            jaeger_exporter = JaegerExporter(
                agent_host_name=settings.JAEGER_AGENT_HOST,
                agent_port=settings.JAEGER_AGENT_PORT,
            )
            provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        except Exception as e:
            logger.warning(f"Failed to initialize Jaeger exporter: {e}")

        # Set global tracer provider
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(__name__)

    return _tracer


def traced(span_name: str) -> Callable[[F], F]:
    """
    Decorator: emit OTel span with token/cost attributes.

    Args:
        span_name: Name of span (e.g., "llm.chat", "vector_db.search")

    Returns:
        Decorated function that emits OTel spans

    Usage:
        >>> @traced("my_task")
        ... async def my_function(...):
        ...     return result
        ...
        >>> # Span will include: tokens_in, tokens_out, usd_cost, latency_ms
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            start_time = time.perf_counter()

            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = await func(*args, **kwargs)

                    # Add latency
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("latency_ms", latency_ms)

                    # If result has token/cost metadata, add it
                    if hasattr(result, "tokens_in"):
                        span.set_attribute("tokens_in", result.tokens_in)
                    if hasattr(result, "tokens_out"):
                        span.set_attribute("tokens_out", result.tokens_out)
                    if hasattr(result, "usd_cost"):
                        span.set_attribute("usd_cost", result.usd_cost)
                    if hasattr(result, "model"):
                        span.set_attribute("model", result.model)
                    if hasattr(result, "cached"):
                        span.set_attribute("cached", result.cached)

                    return result
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            start_time = time.perf_counter()

            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = func(*args, **kwargs)

                    # Add latency
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("latency_ms", latency_ms)

                    # If result has token/cost metadata, add it
                    if hasattr(result, "tokens_in"):
                        span.set_attribute("tokens_in", result.tokens_in)
                    if hasattr(result, "tokens_out"):
                        span.set_attribute("tokens_out", result.tokens_out)
                    if hasattr(result, "usd_cost"):
                        span.set_attribute("usd_cost", result.usd_cost)
                    if hasattr(result, "model"):
                        span.set_attribute("model", result.model)
                    if hasattr(result, "cached"):
                        span.set_attribute("cached", result.cached)

                    return result
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise

        # Return appropriate wrapper based on function type
        if functools.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


class Meters:
    """Prometheus-style metrics (in-memory for now, can export to Prometheus later)."""

    def __init__(self) -> None:
        """Initialize meters."""
        self._tokens_in: dict[str, int] = {}
        self._tokens_out: dict[str, int] = {}
        self._usd_cost: dict[str, float] = {}
        self._cache_hits: dict[str, int] = {}
        self._latencies: dict[str, list[float]] = {}

    def increment_tokens_in(self, tokens: int, model: str) -> None:
        """Increment input token counter."""
        self._tokens_in[model] = self._tokens_in.get(model, 0) + tokens

    def increment_tokens_out(self, tokens: int, model: str) -> None:
        """Increment output token counter."""
        self._tokens_out[model] = self._tokens_out.get(model, 0) + tokens

    def increment_usd_cost(self, cost: float, model: str) -> None:
        """Increment cost counter."""
        self._usd_cost[model] = self._usd_cost.get(model, 0.0) + cost

    def record_latency_ms(self, latency: float, operation: str) -> None:
        """Record operation latency (histogram)."""
        if operation not in self._latencies:
            self._latencies[operation] = []
        self._latencies[operation].append(latency)

    def increment_cache_hits(self, cache_type: str) -> None:
        """Increment cache hit counter (exact or semantic)."""
        key = f"cache_hit_{cache_type}"
        self._cache_hits[key] = self._cache_hits.get(key, 0) + 1

    def get_stats(self) -> dict[str, Any]:
        """Get all collected stats."""
        return {
            "tokens_in": dict(self._tokens_in),
            "tokens_out": dict(self._tokens_out),
            "usd_cost": dict(self._usd_cost),
            "cache_hits": dict(self._cache_hits),
            "latencies": {
                op: {
                    "count": len(vals),
                    "p50": sorted(vals)[len(vals) // 2] if vals else 0,
                    "p99": sorted(vals)[int(len(vals) * 0.99)] if vals else 0,
                }
                for op, vals in self._latencies.items()
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._tokens_in.clear()
        self._tokens_out.clear()
        self._usd_cost.clear()
        self._cache_hits.clear()
        self._latencies.clear()


# Global metrics instance
meters: Meters = Meters()
