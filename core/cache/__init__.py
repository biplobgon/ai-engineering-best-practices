"""
Caching layer: exact-match and semantic caching with Redis.

Design principles:
- Exact cache: hash of (messages, model, params) -> cached response
- Semantic cache: embedding of query -> similar cached queries (cosine sim > threshold)
- Both backed by Redis for sub-millisecond retrieval
- Automatic TTL and invalidation
"""

from typing import Optional, Any


class ExactCache:
    """Hash-based caching: (messages, model, params) -> response."""

    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached response by exact key hash.

        Args:
            key: SHA256 hash of (messages, model, params)

        Returns:
            Cached Response object, or None if miss

        Cost:
            ~0 tokens (Redis lookup)
        """
        raise NotImplementedError

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 86400,
    ) -> None:
        """
        Cache response with TTL.

        Args:
            key: SHA256 hash
            value: Response object to cache
            ttl: Time-to-live in seconds (default: 1 day)
        """
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        """Delete cached entry."""
        raise NotImplementedError

    async def clear_all(self) -> None:
        """Clear all entries."""
        raise NotImplementedError


class SemanticCache:
    """Embedding-based caching: query -> similar cached queries."""

    async def get(
        self,
        query: str,
        threshold: float = 0.93,
    ) -> Optional[Any]:
        """
        Get cached response for semantically similar query.

        Args:
            query: User query text
            threshold: Cosine similarity threshold [0, 1]

        Returns:
            Cached Response if similar query exists, else None

        Cost:
            ~0.001 tokens (embedding only, no LLM call)
        """
        raise NotImplementedError

    async def set(
        self,
        query: str,
        response: Any,
        ttl: int = 86400,
    ) -> None:
        """
        Cache response with embedded query.

        Args:
            query: User query text
            response: Response to cache
            ttl: Time-to-live in seconds
        """
        raise NotImplementedError

    async def set_batch(
        self,
        queries: list[str],
        responses: list[Any],
        ttl: int = 86400,
    ) -> None:
        """Batch cache multiple query-response pairs."""
        raise NotImplementedError

    async def delete(self, query: str) -> None:
        """Delete cached entry by query."""
        raise NotImplementedError


# Global instances
exact_cache: ExactCache = ExactCache()
semantic_cache: SemanticCache = SemanticCache()
