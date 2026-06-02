"""
Semantic cache demo: Exact vs semantic caching comparison.

Shows hit rates, cost savings, latency improvements.
"""

import logging
import time
from typing import Any

from core.cache import exact_cache, semantic_cache
from core.llm import chat, embed
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


async def exact_cached_chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """
    Chat with exact caching.
    
    Args:
        messages: Chat messages
        model: Model name
        **kwargs: Additional args
    
    Returns:
        LLMResponse (cached or fresh)
    
    Example:
        >>> # First call: Cache miss
        >>> r1 = await exact_cached_chat([{"role": "user", "content": "What is Python?"}])
        >>> print(f"Cached: {r1.cached}")  # False
        >>> 
        >>> # Second call: Cache hit
        >>> r2 = await exact_cached_chat([{"role": "user", "content": "What is Python?"}])
        >>> print(f"Cached: {r2.cached}, Latency: {r2.latency_ms}ms")  # True, ~1ms
    """
    # Check exact cache
    cached = await exact_cache.get(messages, model or "default", **kwargs)
    if cached:
        logger.info("Exact cache HIT")
        return cached
    
    logger.info("Exact cache MISS")
    
    # Call LLM
    response = await chat(messages=messages, model=model, **kwargs)
    
    # Store in cache
    await exact_cache.set(messages, model or "default", response, **kwargs)
    
    return response


async def semantic_cached_chat(
    query: str,
    *,
    model: str | None = None,
    threshold: float = 0.93,
    **kwargs: Any,
) -> LLMResponse:
    """
    Chat with semantic caching.
    
    Args:
        query: User query string
        model: Model name
        threshold: Cosine similarity threshold
        **kwargs: Additional args
    
    Returns:
        LLMResponse (semantically cached or fresh)
    
    Example:
        >>> # First query
        >>> r1 = await semantic_cached_chat("How do I reset my password?")
        >>> 
        >>> # Similar query (cache hit even though not exact match)
        >>> r2 = await semantic_cached_chat("How to reset password?")
        >>> print(f"Cached: {r2.cached}")  # True (similarity ≥0.93)
    """
    # Get embedding
    embeddings = await embed([query])
    embedding = embeddings[0]
    
    # Check semantic cache
    cached = await semantic_cache.get(query, embedding, threshold=threshold)
    if cached:
        logger.info(f"Semantic cache HIT (threshold={threshold})")
        return cached
    
    logger.info(f"Semantic cache MISS")
    
    # Call LLM
    messages = [{"role": "user", "content": query}]
    response = await chat(messages=messages, model=model, **kwargs)
    
    # Store in cache
    await semantic_cache.set(query, embedding, response)
    
    return response


async def compare_caching_strategies(
    queries: list[str],
    model: str | None = None,
) -> dict[str, Any]:
    """
    Compare exact vs semantic caching on a set of queries.
    
    Args:
        queries: List of user queries
        model: Model to use
    
    Returns:
        Dict with comparison metrics
    
    Example:
        >>> queries = [
        ...     "What is Python?",
        ...     "What is Python?",  # Exact duplicate
        ...     "What's Python?",   # Semantic similar
        ...     "Tell me about Python",  # Semantic similar
        ...     "What is Rust?",    # Different
        ... ]
        >>> 
        >>> results = await compare_caching_strategies(queries)
        >>> print(f"Exact hit rate: {results['exact_hit_rate']:.0%}")
        >>> print(f"Semantic hit rate: {results['semantic_hit_rate']:.0%}")
    """
    # Clear caches
    await exact_cache.clear_all()
    
    # Exact cache test
    exact_hits = 0
    exact_cost = 0.0
    exact_latency = 0.0
    
    for query in queries:
        messages = [{"role": "user", "content": query}]
        response = await exact_cached_chat(messages, model=model)
        
        if response.cached:
            exact_hits += 1
        
        exact_cost += response.usd_cost
        exact_latency += response.latency_ms
    
    # Semantic cache test (reset)
    await exact_cache.clear_all()
    
    semantic_hits = 0
    semantic_cost = 0.0
    semantic_latency = 0.0
    
    for query in queries:
        response = await semantic_cached_chat(query, model=model)
        
        if response.cached:
            semantic_hits += 1
        
        semantic_cost += response.usd_cost
        semantic_latency += response.latency_ms
    
    # Calculate metrics
    num_queries = len(queries)
    
    return {
        "num_queries": num_queries,
        "exact_hit_rate": exact_hits / num_queries,
        "exact_cost": exact_cost,
        "exact_latency_avg": exact_latency / num_queries,
        "semantic_hit_rate": semantic_hits / num_queries,
        "semantic_cost": semantic_cost,
        "semantic_latency_avg": semantic_latency / num_queries,
        "cost_savings_pct": ((exact_cost - semantic_cost) / exact_cost * 100) if exact_cost > 0 else 0,
        "latency_improvement_pct": ((exact_latency - semantic_latency) / exact_latency * 100) if exact_latency > 0 else 0,
    }
