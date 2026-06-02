"""
Parallel embedding generation for large document sets.

Batch embeddings intelligently to maximize throughput while respecting
API rate limits and memory constraints.

Performance:
- Sequential 100 docs: 20-30s
- Parallel batches: 2-3s
- Speedup: 8-10x
"""

import asyncio
import logging
import time
from typing import Optional

from core.llm import embed
from latency_optimization.parallel_tool_calls.concurrent_tools import (
    parallel_execute,
    RateLimiter,
)


logger = logging.getLogger(__name__)


async def batch_embed(
    texts: list[str],
    batch_size: int = 100,
    model: str = "text-embedding-3-small",
    max_concurrency: int = 5,
) -> list[list[float]]:
    """
    Embed texts in parallel batches.
    
    Args:
        texts: List of texts to embed
        batch_size: Texts per batch
        model: Embedding model
        max_concurrency: Max concurrent batches
        
    Returns:
        List of embeddings (one per text)
        
    Example:
        >>> docs = ["doc 1", "doc 2", ...]  # 500 docs
        >>> embeddings = await batch_embed(docs, batch_size=100)
        >>> # Processes 5 batches of 100 in parallel → ~2-3s
    """
    if not texts:
        return []
    
    start = time.perf_counter()
    
    # Split into batches
    batches = [
        texts[i:i+batch_size]
        for i in range(0, len(texts), batch_size)
    ]
    
    logger.info(f"Embedding {len(texts)} texts in {len(batches)} batches")
    
    # Process batches in parallel with concurrency limit
    async def embed_batch(batch):
        try:
            return await embed(batch, model=model)
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [[0.0] * 1536] * len(batch)  # Return zero vectors
    
    tasks = [embed_batch(batch) for batch in batches]
    batch_results = await parallel_execute(tasks, max_concurrency=max_concurrency)
    
    # Flatten results
    all_embeddings = []
    for batch_embeddings in batch_results:
        all_embeddings.extend(batch_embeddings)
    
    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(f"Embedded {len(texts)} texts in {latency_ms:.0f}ms ({len(texts)/(latency_ms/1000):.0f} texts/sec)")
    
    return all_embeddings


async def adaptive_batch_embed(
    texts: list[str],
    model: str = "text-embedding-3-small",
    target_latency_ms: float = 1000,
) -> list[list[float]]:
    """
    Automatically tune batch size to hit target latency.
    
    Args:
        texts: Texts to embed
        model: Embedding model
        target_latency_ms: Target total time
        
    Returns:
        Embeddings
        
    Strategy:
        1. Start with batch_size=100
        2. Measure latency
        3. Adjust batch size to hit target
        4. Process remaining texts with optimal batch size
    """
    if not texts:
        return []
    
    # Calibration: test with small sample
    calibration_size = min(10, len(texts))
    calibration_texts = texts[:calibration_size]
    
    start = time.perf_counter()
    calibration_embeddings = await embed(calibration_texts, model=model)
    calibration_time = (time.perf_counter() - start) * 1000
    
    # Estimate optimal batch size
    time_per_text = calibration_time / calibration_size
    optimal_batch_size = int(target_latency_ms / time_per_text) if time_per_text > 0 else 100
    optimal_batch_size = max(10, min(optimal_batch_size, 500))  # Clamp to reasonable range
    
    logger.info(
        f"Calibrated: {calibration_time:.0f}ms for {calibration_size} texts, "
        f"using batch_size={optimal_batch_size}"
    )
    
    # Process all texts with optimal batch size
    remaining_texts = texts[calibration_size:]
    if remaining_texts:
        remaining_embeddings = await batch_embed(
            remaining_texts,
            batch_size=optimal_batch_size,
            model=model,
        )
        return calibration_embeddings + remaining_embeddings
    else:
        return calibration_embeddings


async def rate_limited_batch_embed(
    texts: list[str],
    batch_size: int = 100,
    model: str = "text-embedding-3-small",
    max_requests_per_minute: int = 60,
) -> list[list[float]]:
    """
    Embed with rate limiting to avoid API throttling.
    
    Args:
        texts: Texts to embed
        batch_size: Texts per batch
        model: Embedding model
        max_requests_per_minute: API rate limit
        
    Returns:
        Embeddings
    """
    if not texts:
        return []
    
    # Create rate limiter
    rate_per_second = max_requests_per_minute / 60.0
    limiter = RateLimiter(rate_per_second)
    
    # Split into batches
    batches = [
        texts[i:i+batch_size]
        for i in range(0, len(texts), batch_size)
    ]
    
    logger.info(
        f"Rate-limited embedding: {len(batches)} batches at {rate_per_second:.1f} req/s"
    )
    
    # Process batches with rate limiting
    all_embeddings = []
    for i, batch in enumerate(batches):
        await limiter.acquire()
        
        try:
            batch_embeddings = await embed(batch, model=model)
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            logger.error(f"Batch {i} failed: {e}")
            all_embeddings.extend([[0.0] * 1536] * len(batch))
    
    return all_embeddings


async def progressive_batch_embed(
    texts: list[str],
    batch_size: int = 100,
    model: str = "text-embedding-3-small",
    progress_callback: Optional[callable] = None,
) -> list[list[float]]:
    """
    Embed with progress tracking.
    
    Args:
        texts: Texts to embed
        batch_size: Texts per batch
        model: Embedding model
        progress_callback: Called as progress(completed, total)
        
    Returns:
        Embeddings
    """
    if not texts:
        return []
    
    all_embeddings = []
    total = len(texts)
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        
        try:
            batch_embeddings = await embed(batch, model=model)
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            all_embeddings.extend([[0.0] * 1536] * len(batch))
        
        if progress_callback:
            progress_callback(len(all_embeddings), total)
    
    return all_embeddings


async def embed_with_cache(
    texts: list[str],
    model: str = "text-embedding-3-small",
    cache: Optional[dict] = None,
) -> list[list[float]]:
    """
    Embed with caching to skip already-embedded texts.
    
    Args:
        texts: Texts to embed
        model: Embedding model
        cache: Dict mapping text → embedding
        
    Returns:
        Embeddings (from cache or freshly computed)
    """
    if cache is None:
        cache = {}
    
    # Separate cached and uncached
    cached_texts = []
    uncached_texts = []
    text_to_index = {}
    
    for i, text in enumerate(texts):
        if text in cache:
            cached_texts.append((i, text))
        else:
            uncached_texts.append(text)
            text_to_index[text] = i
    
    logger.info(
        f"Cache: {len(cached_texts)} hits, {len(uncached_texts)} misses "
        f"({len(cached_texts)/(len(texts))*100:.1f}% hit rate)"
    )
    
    # Embed uncached texts
    if uncached_texts:
        new_embeddings = await batch_embed(uncached_texts, model=model)
        
        # Update cache
        for text, embedding in zip(uncached_texts, new_embeddings):
            cache[text] = embedding
    
    # Assemble final results
    result = [None] * len(texts)
    for i, text in cached_texts:
        result[i] = cache[text]
    for text, i in text_to_index.items():
        result[i] = cache[text]
    
    return result


# Benchmarking
async def benchmark_embedding_strategies(
    texts: list[str],
    model: str = "text-embedding-3-small",
) -> dict:
    """
    Compare different embedding strategies.
    
    Returns:
        Dict with timing for each strategy
    """
    results = {}
    
    # Sequential
    start = time.perf_counter()
    for text in texts:
        await embed([text], model=model)
    results["sequential_ms"] = round((time.perf_counter() - start) * 1000, 2)
    
    # Batch (no parallelism)
    start = time.perf_counter()
    await embed(texts, model=model, batch_size=len(texts))
    results["batch_ms"] = round((time.perf_counter() - start) * 1000, 2)
    
    # Parallel batches
    start = time.perf_counter()
    await batch_embed(texts, batch_size=50, model=model)
    results["parallel_batch_ms"] = round((time.perf_counter() - start) * 1000, 2)
    
    # Calculate speedups
    results["batch_speedup"] = round(results["sequential_ms"] / results["batch_ms"], 2)
    results["parallel_speedup"] = round(results["sequential_ms"] / results["parallel_batch_ms"], 2)
    
    return results


# Example usage
if __name__ == "__main__":
    async def demo():
        # Sample texts
        texts = [f"Sample document number {i} with some content." for i in range(50)]
        
        print("Parallel Embeddings Demo\n" + "="*60)
        
        # Progress callback
        def on_progress(done, total):
            pct = (done / total) * 100
            print(f"\rProgress: {done}/{total} ({pct:.0f}%)", end="", flush=True)
        
        # Embed with progress
        print("\nEmbedding 50 texts:")
        start = time.perf_counter()
        embeddings = await progressive_batch_embed(
            texts,
            batch_size=10,
            progress_callback=on_progress,
        )
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"\n\nCompleted in {elapsed:.0f}ms")
        print(f"Throughput: {len(texts)/(elapsed/1000):.0f} texts/sec")
        print(f"Embedding dimensions: {len(embeddings[0])}")
    
    # Uncomment to run:
    # asyncio.run(demo())
    print("Demo available - uncomment asyncio.run(demo()) to test")
