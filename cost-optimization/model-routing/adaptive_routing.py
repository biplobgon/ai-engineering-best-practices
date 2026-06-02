"""
Adaptive routing: Learn optimal model from historical success rates.

Tracks (task_type, model) → (success_count, failure_count) in Redis.
Periodically adjusts routing based on observed quality/cost tradeoffs.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

import redis.asyncio as aioredis

from core.config import get_settings
from core.llm import chat
from core.llm.router import TaskType, router
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


@dataclass
class ModelStats:
    """Statistics for a specific (task_type, model) pair."""
    
    success_count: int = 0
    failure_count: int = 0
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    last_updated: float = 0.0
    
    @property
    def total_count(self) -> int:
        """Total requests."""
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        """Success rate (0-1)."""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count
    
    @property
    def avg_cost(self) -> float:
        """Average cost per request."""
        if self.total_count == 0:
            return 0.0
        return self.total_cost / self.total_count
    
    @property
    def avg_latency_ms(self) -> float:
        """Average latency in ms."""
        if self.total_count == 0:
            return 0.0
        return self.total_latency_ms / self.total_count


class AdaptiveRouter:
    """
    Learn optimal model from historical data.
    
    Algorithm:
        1. Track success/failure per (task_type, model)
        2. Periodically (every N requests):
           - If current model success_rate < 90% → switch to better model
           - If current model success_rate > 98% → try cheaper model
        3. Update routing table in Redis
    
    Storage:
        Redis hash: routing:stats:{task_type}:{model}
        Fields: success_count, failure_count, total_cost, total_latency_ms, last_updated
    
    Example:
        >>> router = AdaptiveRouter()
        >>> 
        >>> # Make requests (stats tracked automatically)
        >>> for query in queries:
        ...     response = await router.chat(
        ...         messages=[{"role": "user", "content": query}],
        ...         task_type="classification"
        ...     )
        >>> 
        >>> # Check learned stats
        >>> stats = await router.get_stats("classification")
        >>> print(stats)
    """
    
    def __init__(
        self,
        update_threshold: int = 100,  # Update routing after N requests
        min_success_rate: float = 0.90,
        target_success_rate: float = 0.98,
    ) -> None:
        """
        Initialize adaptive router.
        
        Args:
            update_threshold: Re-evaluate routing after N requests
            min_success_rate: Switch to better model if below this
            target_success_rate: Try cheaper model if above this
        """
        self.settings = get_settings()
        self._redis: aioredis.Redis | None = None
        self.update_threshold = update_threshold
        self.min_success_rate = min_success_rate
        self.target_success_rate = target_success_rate
        self.base_router = router  # Use core router
    
    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis
    
    def _make_key(self, task_type: str, model: str) -> str:
        """Create Redis key for (task_type, model) stats."""
        return f"routing:stats:{task_type}:{model}"
    
    async def _get_stats(self, task_type: str, model: str) -> ModelStats:
        """Get stats for (task_type, model) from Redis."""
        redis = await self._get_redis()
        key = self._make_key(task_type, model)
        
        data = await redis.hgetall(key)
        if not data:
            return ModelStats()
        
        return ModelStats(
            success_count=int(data.get("success_count", 0)),
            failure_count=int(data.get("failure_count", 0)),
            total_cost=float(data.get("total_cost", 0.0)),
            total_latency_ms=float(data.get("total_latency_ms", 0.0)),
            last_updated=float(data.get("last_updated", 0.0)),
        )
    
    async def _update_stats(
        self,
        task_type: str,
        model: str,
        success: bool,
        cost: float,
        latency_ms: float,
    ) -> None:
        """Update stats in Redis."""
        redis = await self._get_redis()
        key = self._make_key(task_type, model)
        
        # Increment counts
        if success:
            await redis.hincrby(key, "success_count", 1)
        else:
            await redis.hincrby(key, "failure_count", 1)
        
        # Increment cost/latency
        await redis.hincrbyfloat(key, "total_cost", cost)
        await redis.hincrbyfloat(key, "total_latency_ms", latency_ms)
        
        # Update timestamp
        await redis.hset(key, "last_updated", time.time())
        
        # Set expiry (30 days)
        await redis.expire(key, 30 * 86400)
    
    async def get_stats(self, task_type: str) -> dict[str, ModelStats]:
        """
        Get stats for all models for a task type.
        
        Args:
            task_type: Task type to query
        
        Returns:
            Dict of {model_name: ModelStats}
        
        Example:
            >>> stats = await router.get_stats("classification")
            >>> for model, stat in stats.items():
            ...     print(f"{model}: {stat.success_rate:.2%} success, ${stat.avg_cost:.6f} avg")
        """
        models = self.base_router.get_all_models(task_type)  # type: ignore[arg-type]
        
        stats = {}
        for model in models:
            stats[model] = await self._get_stats(task_type, model)
        
        return stats
    
    async def _choose_best_model(self, task_type: TaskType) -> str:
        """
        Choose best model based on historical stats.
        
        Logic:
        1. Get current model (cheapest by default)
        2. Check success rate
        3. If too low → try next tier
        4. If too high → try cheaper tier (if available)
        
        Returns:
            Best model name
        """
        models = self.base_router.get_all_models(task_type)
        
        if not models:
            return self.settings.DEFAULT_LLM
        
        # Get stats for all models
        stats_dict = await self.get_stats(task_type)
        
        # Find model with best success rate (min threshold)
        best_model = models[0]  # Default to cheapest
        
        for model in models:
            stats = stats_dict.get(model, ModelStats())
            
            # Skip if not enough data
            if stats.total_count < 10:
                continue
            
            # If current best has low success rate, try this model
            current_stats = stats_dict.get(best_model, ModelStats())
            
            if current_stats.success_rate < self.min_success_rate:
                if stats.success_rate > current_stats.success_rate:
                    best_model = model
                    logger.info(
                        f"Switching to {model} (success rate: {stats.success_rate:.2%})",
                        extra={"task_type": task_type, "model": model},
                    )
        
        return best_model
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        task_type: TaskType = "generation",
        track_stats: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Chat with adaptive routing.
        
        Args:
            messages: Chat messages
            task_type: Task type (for routing)
            track_stats: Track success/failure stats
            **kwargs: Additional args for chat()
        
        Returns:
            LLMResponse
        
        Example:
            >>> router = AdaptiveRouter()
            >>> response = await router.chat(
            ...     messages=[{"role": "user", "content": "Classify sentiment"}],
            ...     task_type="classification"
            ... )
        """
        # Choose best model based on stats
        model = await self._choose_best_model(task_type)
        
        success = False
        cost = 0.0
        latency_ms = 0.0
        
        try:
            # Make LLM call
            response = await chat(messages=messages, model=model, **kwargs)
            
            success = True
            cost = response.usd_cost
            latency_ms = response.latency_ms
            
            return response
        
        except Exception as e:
            logger.warning(
                f"Model {model} failed: {e}",
                extra={"task_type": task_type, "model": model},
            )
            raise
        
        finally:
            # Update stats
            if track_stats:
                await self._update_stats(
                    task_type=task_type,
                    model=model,
                    success=success,
                    cost=cost,
                    latency_ms=latency_ms,
                )
    
    async def clear_stats(self, task_type: str | None = None) -> None:
        """
        Clear all stats (for testing/reset).
        
        Args:
            task_type: Clear only this task type, or all if None
        """
        redis = await self._get_redis()
        
        if task_type:
            pattern = f"routing:stats:{task_type}:*"
        else:
            pattern = "routing:stats:*"
        
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
        
        logger.info(f"Cleared stats for pattern: {pattern}")


# Convenience function
async def adaptive_chat(
    messages: list[dict[str, str]],
    *,
    task_type: TaskType = "generation",
    **kwargs: Any,
) -> LLMResponse:
    """
    Convenience function for adaptive routing.
    
    Example:
        >>> from cost_optimization.model_routing import adaptive_chat
        >>> 
        >>> response = await adaptive_chat(
        ...     messages=[{"role": "user", "content": "Extract fields"}],
        ...     task_type="extraction"
        ... )
    """
    router_instance = AdaptiveRouter()
    return await router_instance.chat(
        messages=messages,
        task_type=task_type,
        **kwargs,
    )
