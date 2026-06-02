"""
Concurrent tool execution patterns using asyncio.

Run independent operations in parallel to reduce total latency.
Critical for multi-step agents and RAG systems.

Performance:
- Reduction: 60-80% for independent operations
- Example: 5 sequential calls (15s) → 5 parallel calls (4s) = 3.75x faster
"""

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, Optional

from core.telemetry import meters


logger = logging.getLogger(__name__)


async def parallel_execute(
    tasks: list[Coroutine],
    *,
    max_concurrency: Optional[int] = None,
    return_exceptions: bool = False,
) -> list[Any]:
    """
    Execute multiple async tasks in parallel.
    
    Args:
        tasks: List of coroutines to execute
        max_concurrency: Optional limit on concurrent tasks
        return_exceptions: If True, exceptions are returned instead of raised
        
    Returns:
        List of results (or exceptions if return_exceptions=True)
        
    Example:
        >>> tasks = [
        ...     embed("text 1"),
        ...     embed("text 2"),
        ...     embed("text 3"),
        ... ]
        >>> results = await parallel_execute(tasks)
    """
    if not tasks:
        return []
    
    start = time.perf_counter()
    
    if max_concurrency:
        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def bounded_task(coro):
            async with semaphore:
                return await coro
        
        tasks = [bounded_task(task) for task in tasks]
    
    results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    
    latency_ms = (time.perf_counter() - start) * 1000
    
    meters.record_latency_ms(latency_ms, "parallel.execute")
    meters.increment("parallel.tasks", len(tasks))
    
    logger.info(f"Executed {len(tasks)} tasks in parallel: {latency_ms:.0f}ms")
    
    return results


async def parallel_map(
    func: Callable[[Any], Coroutine],
    items: list[Any],
    *,
    max_concurrency: int = 10,
) -> list[Any]:
    """
    Map async function over list of items in parallel.
    
    Args:
        func: Async function to apply
        items: Items to process
        max_concurrency: Max concurrent operations
        
    Returns:
        List of results
        
    Example:
        >>> async def process(item):
        ...     return await some_api_call(item)
        >>> results = await parallel_map(process, items)
    """
    tasks = [func(item) for item in items]
    return await parallel_execute(tasks, max_concurrency=max_concurrency)


async def parallel_with_timeout(
    tasks: list[Coroutine],
    timeout_seconds: float,
    *,
    default_value: Any = None,
) -> list[Any]:
    """
    Execute tasks in parallel with a timeout.
    
    Args:
        tasks: Coroutines to execute
        timeout_seconds: Max time to wait
        default_value: Value to return for timed-out tasks
        
    Returns:
        List of results (default_value for timed-out tasks)
    """
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=timeout_seconds,
        )
        return results
    except asyncio.TimeoutError:
        logger.warning(f"Parallel execution timed out after {timeout_seconds}s")
        return [default_value] * len(tasks)


async def parallel_with_fallback(
    primary_tasks: list[Coroutine],
    fallback_tasks: list[Coroutine],
    timeout_seconds: float = 5.0,
) -> list[Any]:
    """
    Execute primary tasks, fall back to alternatives on failure/timeout.
    
    Args:
        primary_tasks: Preferred operations
        fallback_tasks: Fallback operations (same length as primary)
        timeout_seconds: Max time for primary tasks
        
    Returns:
        Results from primary or fallback tasks
        
    Example:
        >>> # Try fast model, fall back to slow but reliable model
        >>> primary = [chat(msg, model="gpt-4o-mini") for msg in messages]
        >>> fallback = [chat(msg, model="gpt-3.5-turbo") for msg in messages]
        >>> results = await parallel_with_fallback(primary, fallback)
    """
    assert len(primary_tasks) == len(fallback_tasks)
    
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*primary_tasks, return_exceptions=True),
            timeout=timeout_seconds,
        )
        
        # Check for failures and retry with fallback
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Task {i} failed, using fallback")
                fallback_result = await fallback_tasks[i]
                final_results.append(fallback_result)
            else:
                final_results.append(result)
        
        return final_results
        
    except asyncio.TimeoutError:
        logger.warning("Primary tasks timed out, using fallback")
        return await asyncio.gather(*fallback_tasks)


async def batch_with_progress(
    func: Callable[[Any], Coroutine],
    items: list[Any],
    batch_size: int = 10,
    *,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[Any]:
    """
    Process items in batches with progress tracking.
    
    Args:
        func: Async function to apply
        items: Items to process
        batch_size: Items per batch
        progress_callback: Optional callback(completed, total)
        
    Returns:
        List of results
        
    Example:
        >>> def on_progress(done, total):
        ...     print(f"Progress: {done}/{total}")
        >>> results = await batch_with_progress(
        ...     process_item,
        ...     items,
        ...     batch_size=10,
        ...     progress_callback=on_progress,
        ... )
    """
    results = []
    total = len(items)
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_tasks = [func(item) for item in batch]
        
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)
        
        if progress_callback:
            progress_callback(len(results), total)
    
    return results


class RateLimiter:
    """
    Rate limiter for parallel operations.
    
    Ensures operations don't exceed a specified rate (ops/second).
    """
    
    def __init__(self, rate: float):
        """
        Args:
            rate: Maximum operations per second
        """
        self.rate = rate
        self.min_interval = 1.0 / rate
        self.last_call = 0.0
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until operation is allowed by rate limit."""
        async with self.lock:
            now = time.perf_counter()
            time_since_last = now - self.last_call
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                await asyncio.sleep(wait_time)
            
            self.last_call = time.perf_counter()


async def rate_limited_parallel(
    func: Callable[[Any], Coroutine],
    items: list[Any],
    rate: float = 10.0,
) -> list[Any]:
    """
    Execute operations in parallel with rate limiting.
    
    Args:
        func: Async function to apply
        items: Items to process
        rate: Max operations per second
        
    Returns:
        List of results
        
    Example:
        >>> # Max 10 API calls per second
        >>> results = await rate_limited_parallel(
        ...     api_call,
        ...     items,
        ...     rate=10.0,
        ... )
    """
    limiter = RateLimiter(rate)
    
    async def limited_func(item):
        await limiter.acquire()
        return await func(item)
    
    tasks = [limited_func(item) for item in items]
    return await asyncio.gather(*tasks)


# Benchmarking utilities
async def benchmark_parallel_vs_sequential(
    func: Callable[[Any], Coroutine],
    items: list[Any],
) -> dict:
    """
    Compare parallel vs sequential execution.
    
    Returns:
        Dict with timing metrics and speedup
    """
    # Sequential
    start = time.perf_counter()
    sequential_results = []
    for item in items:
        result = await func(item)
        sequential_results.append(result)
    sequential_time = time.perf_counter() - start
    
    # Parallel
    start = time.perf_counter()
    tasks = [func(item) for item in items]
    parallel_results = await asyncio.gather(*tasks)
    parallel_time = time.perf_counter() - start
    
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    
    return {
        "sequential_time_ms": round(sequential_time * 1000, 2),
        "parallel_time_ms": round(parallel_time * 1000, 2),
        "speedup": round(speedup, 2),
        "items_processed": len(items),
    }


# Example usage
if __name__ == "__main__":
    async def demo():
        # Simulate async operations
        async def mock_api_call(item: str) -> str:
            await asyncio.sleep(0.5)  # Simulate 500ms API call
            return f"Processed: {item}"
        
        items = [f"item_{i}" for i in range(10)]
        
        print("Parallel Execution Demo\n" + "="*60)
        
        # Benchmark
        metrics = await benchmark_parallel_vs_sequential(mock_api_call, items[:5])
        
        print(f"\nSequential: {metrics['sequential_time_ms']}ms")
        print(f"Parallel: {metrics['parallel_time_ms']}ms")
        print(f"Speedup: {metrics['speedup']}x")
        
        # Rate-limited
        print("\n\nRate-limited execution (2 ops/sec):")
        start = time.perf_counter()
        results = await rate_limited_parallel(mock_api_call, items[:5], rate=2.0)
        elapsed = time.perf_counter() - start
        print(f"Time: {elapsed:.1f}s (expected ~2.5s for 5 items at 2 ops/sec)")
    
    # Uncomment to run:
    # asyncio.run(demo())
    print("Demo available - uncomment asyncio.run(demo()) to test")
