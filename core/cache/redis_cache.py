"""
Redis-backed caching (exact + semantic).

Exact cache: hash-based lookup
Semantic cache: embedding-based similarity search
"""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis
from sklearn.metrics.pairwise import cosine_similarity

from core.config import get_settings
from core.schemas import LLMResponse
from core.telemetry import meters


logger = logging.getLogger(__name__)


class ExactCache:
    """Hash-based exact caching using Redis."""

    def __init__(self) -> None:
        """Initialize exact cache."""
        self.settings = get_settings()
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _make_key(self, messages: list[dict[str, str]], model: str, **params: Any) -> str:
        """Create cache key from messages + model + params."""
        # Serialize to stable JSON
        cache_input = {
            "messages": messages,
            "model": model,
            **params,
        }
        serialized = json.dumps(cache_input, sort_keys=True)
        hash_key = hashlib.sha256(serialized.encode()).hexdigest()
        return f"exact:{hash_key}"

    async def get(
        self,
        messages: list[dict[str, str]],
        model: str,
        **params: Any,
    ) -> LLMResponse | None:
        """
        Get cached response by exact match.

        Args:
            messages: Chat messages
            model: Model name
            **params: Other parameters (temp, max_tokens, etc.)

        Returns:
            Cached LLMResponse or None if miss
        """
        if not self.settings.ENABLE_CACHE:
            return None

        try:
            redis = await self._get_redis()
            key = self._make_key(messages, model, **params)

            cached_json = await redis.get(key)
            if cached_json:
                meters.increment_cache_hits("exact")
                logger.debug(f"Exact cache HIT: {key[:16]}...")

                # Deserialize
                data = json.loads(cached_json)
                response = LLMResponse(**data)
                response.cached = True
                return response

            logger.debug(f"Exact cache MISS: {key[:16]}...")
            return None

        except Exception as e:
            logger.warning(f"Exact cache GET failed: {e}")
            return None

    async def set(
        self,
        messages: list[dict[str, str]],
        model: str,
        response: LLMResponse,
        ttl: int | None = None,
        **params: Any,
    ) -> None:
        """
        Cache response with TTL.

        Args:
            messages: Chat messages
            model: Model name
            response: Response to cache
            ttl: Time-to-live in seconds (default: config CACHE_TTL)
            **params: Other parameters
        """
        if not self.settings.ENABLE_CACHE:
            return

        try:
            redis = await self._get_redis()
            key = self._make_key(messages, model, **params)
            ttl = ttl or self.settings.CACHE_TTL

            # Serialize
            response_dict = response.model_dump()
            response_json = json.dumps(response_dict)

            await redis.setex(key, ttl, response_json)
            logger.debug(f"Exact cache SET: {key[:16]}... (TTL={ttl}s)")

        except Exception as e:
            logger.warning(f"Exact cache SET failed: {e}")

    async def delete(self, messages: list[dict[str, str]], model: str, **params: Any) -> None:
        """Delete cached entry."""
        try:
            redis = await self._get_redis()
            key = self._make_key(messages, model, **params)
            await redis.delete(key)
        except Exception as e:
            logger.warning(f"Exact cache DELETE failed: {e}")

    async def clear_all(self) -> None:
        """Clear all cached entries."""
        try:
            redis = await self._get_redis()
            # Delete all keys matching pattern
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match="exact:*", count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Exact cache cleared")
        except Exception as e:
            logger.warning(f"Exact cache CLEAR failed: {e}")


class SemanticCache:
    """Embedding-based semantic caching using Redis + cosine similarity."""

    def __init__(self) -> None:
        """Initialize semantic cache."""
        self.settings = get_settings()
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # Binary mode for embeddings
            )
        return self._redis

    async def get(
        self,
        query: str,
        embedding: list[float],
        threshold: float | None = None,
    ) -> LLMResponse | None:
        """
        Get cached response for semantically similar query.

        Args:
            query: User query text
            embedding: Query embedding vector
            threshold: Cosine similarity threshold (default: config threshold)

        Returns:
            Cached Response if similar query exists, else None
        """
        if not self.settings.ENABLE_CACHE:
            return None

        threshold = threshold or self.settings.SEMANTIC_CACHE_THRESHOLD

        try:
            redis = await self._get_redis()

            # Get all semantic cache entries
            cursor = 0
            best_match: tuple[float, LLMResponse] | None = None

            while True:
                cursor, keys = await redis.scan(cursor, match="semantic:*", count=100)

                for key in keys:
                    data = await redis.get(key)
                    if not data:
                        continue

                    # Deserialize
                    cached = json.loads(data)
                    cached_embedding = cached.get("embedding", [])
                    cached_response_dict = cached.get("response", {})

                    if not cached_embedding or not cached_response_dict:
                        continue

                    # Compute cosine similarity
                    similarity = cosine_similarity(
                        [embedding],
                        [cached_embedding],
                    )[0][0]

                    if similarity >= threshold:
                        if best_match is None or similarity > best_match[0]:
                            response = LLMResponse(**cached_response_dict)
                            best_match = (similarity, response)

                if cursor == 0:
                    break

            if best_match:
                meters.increment_cache_hits("semantic")
                logger.debug(f"Semantic cache HIT (similarity={best_match[0]:.3f})")
                response = best_match[1]
                response.cached = True
                return response

            logger.debug("Semantic cache MISS")
            return None

        except Exception as e:
            logger.warning(f"Semantic cache GET failed: {e}")
            return None

    async def set(
        self,
        query: str,
        embedding: list[float],
        response: LLMResponse,
        ttl: int | None = None,
    ) -> None:
        """
        Cache response with embedded query.

        Args:
            query: User query text
            embedding: Query embedding vector
            response: Response to cache
            ttl: Time-to-live in seconds
        """
        if not self.settings.ENABLE_CACHE:
            return

        try:
            redis = await self._get_redis()
            ttl = ttl or self.settings.CACHE_TTL

            # Create key from query hash
            query_hash = hashlib.sha256(query.encode()).hexdigest()
            key = f"semantic:{query_hash}"

            # Serialize
            cache_data = {
                "query": query,
                "embedding": embedding,
                "response": response.model_dump(),
            }
            cache_json = json.dumps(cache_data)

            await redis.setex(key, ttl, cache_json)
            logger.debug(f"Semantic cache SET: {key[:24]}... (TTL={ttl}s)")

        except Exception as e:
            logger.warning(f"Semantic cache SET failed: {e}")


# Global instances
exact_cache = ExactCache()
semantic_cache = SemanticCache()
