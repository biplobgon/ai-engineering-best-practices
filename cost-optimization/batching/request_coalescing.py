"""
Request coalescing: Dedupe identical in-flight requests.

For FAQ bots or high-duplicate workloads → 50-90% cost reduction.
"""

import asyncio
import hashlib
import json
import logging
from typing import Any, Callable, TypeVar


logger = logging.getLogger(__name__)

T = TypeVar("T")


class CoalescingCache:
    """
    Coalesce identical in-flight requests to avoid duplicate work.
    
    Example:
        >>> cache = CoalescingCache()
        >>> 
        >>> # 10 users ask same question simultaneously
        >>> tasks = [
        ...     cache.get_or_compute("What is Python?", lambda: expensive_llm_call())
        ...     for _ in range(10)
        ... ]
        >>> results = await asyncio.gather(*tasks)
        >>> # Only 1 LLM call, result shared across all 10
    """
    
    def __init__(self) -> None:
        """Initialize coalescing cache."""
        self._in_flight: dict[str, asyncio.Future[Any]] = {}
        self._lock = asyncio.Lock()
    
    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """Create cache key from args/kwargs."""
        # Serialize to stable JSON
        key_data = {"args": args, "kwargs": kwargs}
        serialized = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
    ) -> Any:
        """
        Get result or compute if not in flight.
        
        Args:
            key: Cache key (e.g., query string)
            compute_fn: Async function to compute result
        
        Returns:
            Result from cache or compute_fn
        """
        async with self._lock:
            # Check if already in flight
            if key in self._in_flight:
                logger.debug(f"Coalescing request: {key[:16]}...")
                future = self._in_flight[key]
            else:
                # Start new computation
                logger.debug(f"Starting computation: {key[:16]}...")
                future = asyncio.create_task(compute_fn())
                self._in_flight[key] = future  # type: ignore[assignment]
        
        try:
            # Wait for result
            result = await future
            return result
        finally:
            # Remove from in-flight
            async with self._lock:
                if key in self._in_flight:
                    del self._in_flight[key]


# Convenience functions
_global_cache = CoalescingCache()


async def coalesced_call(
    key: str,
    compute_fn: Callable[[], T],
) -> T:
    """
    Global coalescing cache convenience function.
    
    Example:
        >>> from cost_optimization.batching import coalesced_call
        >>> 
        >>> async def expensive_operation():
        ...     return await chat([{"role": "user", "content": "What is Python?"}])
        >>> 
        >>> # Multiple calls with same key → only 1 execution
        >>> result = await coalesced_call("what-is-python", expensive_operation)
    """
    return await _global_cache.get_or_compute(key, compute_fn)
