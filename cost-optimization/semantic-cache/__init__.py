"""
Semantic caching for cost reduction.

Exports:
- exact_cached_chat: Exact cache wrapper
- semantic_cached_chat: Semantic cache wrapper
- compare_caching_strategies: Benchmark caching strategies
"""

from cost_optimization.semantic_cache.cache_demo import (
    exact_cached_chat,
    semantic_cached_chat,
    compare_caching_strategies,
)


__all__ = [
    "exact_cached_chat",
    "semantic_cached_chat",
    "compare_caching_strategies",
]
