"""
Cost Optimization Module

Reduce LLM costs by 60-95% through:
- Model routing (cheap-first, fallback)
- Semantic caching (40-60% hit rate)
- Batching (10-100x throughput)
- Prompt caching (90% savings on repeated context)

Quick Start:
    >>> from cost_optimization.model_routing import cheap_first_chat
    >>> from cost_optimization.batching import batch_chat
    >>> from cost_optimization.semantic_cache import semantic_cached_chat
    >>> from cost_optimization.prompt_caching import anthropic_cached_chat
    >>> 
    >>> # Cheap-first routing
    >>> response = await cheap_first_chat(
    ...     messages=[{"role": "user", "content": "Classify sentiment"}],
    ...     task_type="classification"
    ... )
    >>> 
    >>> # Batch processing
    >>> responses = await batch_chat(queries, max_concurrency=50)
    >>> 
    >>> # Semantic caching
    >>> response = await semantic_cached_chat("How to reset password?")
    >>> 
    >>> # Prompt caching
    >>> response = await anthropic_cached_chat(
    ...     messages=[{"role": "user", "content": "Q1"}],
    ...     system="Large system message..."
    ... )
"""

# Model routing
from cost_optimization.model_routing import (
    CheapFirstRouter,
    FallbackRouter,
    AdaptiveRouter,
    cheap_first_chat,
    fallback_chat,
    adaptive_chat,
)

# Batching
from cost_optimization.batching import (
    batch_chat,
    batch_embed,
    ConcurrentBatcher,
    AdaptiveBatcher,
    CoalescingCache,
)

# Semantic caching
from cost_optimization.semantic_cache import (
    exact_cached_chat,
    semantic_cached_chat,
    compare_caching_strategies,
)

# Prompt caching
from cost_optimization.prompt_caching import (
    anthropic_cached_chat,
    estimate_cache_savings,
)


__all__ = [
    # Model routing
    "CheapFirstRouter",
    "FallbackRouter",
    "AdaptiveRouter",
    "cheap_first_chat",
    "fallback_chat",
    "adaptive_chat",
    # Batching
    "batch_chat",
    "batch_embed",
    "ConcurrentBatcher",
    "AdaptiveBatcher",
    "CoalescingCache",
    # Semantic caching
    "exact_cached_chat",
    "semantic_cached_chat",
    "compare_caching_strategies",
    # Prompt caching
    "anthropic_cached_chat",
    "estimate_cache_savings",
]
