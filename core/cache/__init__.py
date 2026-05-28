"""
Caching layer: exact-match and semantic caching with Redis.

Design principles:
- Exact cache: hash of (messages, model, params) -> cached response
- Semantic cache: embedding of query -> similar cached queries (cosine sim > threshold)
- Both backed by Redis for sub-millisecond retrieval
- Automatic TTL and invalidation
"""

from core.cache.redis_cache import ExactCache, SemanticCache, exact_cache, semantic_cache


__all__ = [
    "ExactCache",
    "SemanticCache",
    "exact_cache",
    "semantic_cache",
]
