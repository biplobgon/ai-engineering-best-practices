"""
Concurrent LLM calls with asyncio.gather() and rate limiting.

Speedup: 10-100x faster than sequential
Cost: Same (or slightly cheaper)
"""

import asyncio
import logging
from typing import Any, Callable

from core.llm import chat
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


class ConcurrentBatcher:
    """
    Execute LLM calls concurrently with rate limiting.
    
    Example:
        >>> batcher = ConcurrentBatcher(max_concurrency=50)
        >>> responses = await batcher.batch_chat(
        ...     queries=["Query 1", "Query 2", ..., "Query 100"],
        ...     model="claude-3-5-haiku"
        ... )
        >>> print(f"Processed {len(responses)} in parallel")
    """
    
    def __init__(self, max_concurrency: int = 50) -> None:
        """
        Initialize concurrent batcher.
        
        Args:
            max_concurrency: Maximum concurrent requests (default: 50)
        """
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    async def _rate_limited_chat(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse | Exception:
        """
        Chat with rate limiting.
        
        Args:
            messages: Chat messages
            **kwargs: Additional args for chat()
        
        Returns:
            LLMResponse or Exception if failed
        """
        async with self.semaphore:
            try:
                return await chat(messages=messages, **kwargs)
            except Exception as e:
                logger.warning(f"Request failed: {e}")
                return e
    
    async def batch_chat(
        self,
        queries: list[str],
        *,
        model: str | None = None,
        return_exceptions: bool = True,
        **kwargs: Any,
    ) -> list[LLMResponse | Exception]:
        """
        Batch chat requests with concurrency control.
        
        Args:
            queries: List of query strings
            model: Model to use (default: config DEFAULT_LLM)
            return_exceptions: Return exceptions instead of raising
            **kwargs: Additional args for chat()
        
        Returns:
            List of LLMResponse (or Exception if return_exceptions=True)
        
        Example:
            >>> batcher = ConcurrentBatcher(max_concurrency=50)
            >>> responses = await batcher.batch_chat(
            ...     queries=["What is Python?", "What is Rust?"],
            ...     model="claude-3-5-haiku"
            ... )
        
        Performance:
            100 queries @ 200ms each:
            - Sequential: 20 seconds
            - Parallel (50 concurrent): 4 seconds
            - Speedup: 5x
        """
        # Convert queries to messages format
        messages_list = [
            [{"role": "user", "content": query}]
            for query in queries
        ]
        
        # Create tasks
        tasks = [
            self._rate_limited_chat(messages, model=model, **kwargs)
            for messages in messages_list
        ]
        
        logger.info(
            f"Batching {len(tasks)} requests (max_concurrency={self.max_concurrency})",
            extra={"num_requests": len(tasks), "max_concurrency": self.max_concurrency},
        )
        
        # Execute in parallel
        if return_exceptions:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = await asyncio.gather(*tasks)
        
        # Count successes/failures
        successes = sum(1 for r in results if isinstance(r, LLMResponse))
        failures = len(results) - successes
        
        logger.info(
            f"Batch complete: {successes} success, {failures} failures",
            extra={"successes": successes, "failures": failures},
        )
        
        return results  # type: ignore[return-value]
    
    async def batch_chat_with_messages(
        self,
        messages_list: list[list[dict[str, str]]],
        *,
        model: str | None = None,
        return_exceptions: bool = True,
        **kwargs: Any,
    ) -> list[LLMResponse | Exception]:
        """
        Batch chat with custom messages (not just strings).
        
        Args:
            messages_list: List of message lists
            model: Model to use
            return_exceptions: Return exceptions instead of raising
            **kwargs: Additional args
        
        Returns:
            List of LLMResponse (or Exception)
        
        Example:
            >>> messages_list = [
            ...     [
            ...         {"role": "system", "content": "You are helpful"},
            ...         {"role": "user", "content": "Question 1"}
            ...     ],
            ...     [
            ...         {"role": "system", "content": "You are helpful"},
            ...         {"role": "user", "content": "Question 2"}
            ...     ],
            ... ]
            >>> responses = await batcher.batch_chat_with_messages(messages_list)
        """
        tasks = [
            self._rate_limited_chat(messages, model=model, **kwargs)
            for messages in messages_list
        ]
        
        if return_exceptions:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = await asyncio.gather(*tasks)
        
        return results  # type: ignore[return-value]


class AdaptiveBatcher:
    """
    Adaptive batching that adjusts concurrency based on rate limits.
    
    Automatically reduces concurrency on 429 errors, increases on success.
    
    Example:
        >>> batcher = AdaptiveBatcher(initial_concurrency=50)
        >>> responses = await batcher.batch_chat(queries)
        >>> print(f"Final concurrency: {batcher.current_concurrency}")
    """
    
    def __init__(
        self,
        initial_concurrency: int = 50,
        min_concurrency: int = 10,
        max_concurrency: int = 200,
    ) -> None:
        """
        Initialize adaptive batcher.
        
        Args:
            initial_concurrency: Starting concurrency
            min_concurrency: Minimum concurrency (safety floor)
            max_concurrency: Maximum concurrency (safety ceiling)
        """
        self.current_concurrency = initial_concurrency
        self.min_concurrency = min_concurrency
        self.max_concurrency = max_concurrency
    
    def _adjust_concurrency(self, rate_limit_rate: float) -> None:
        """
        Adjust concurrency based on rate limit errors.
        
        Args:
            rate_limit_rate: Fraction of requests that hit rate limits (0-1)
        """
        if rate_limit_rate > 0.1:  # >10% rate limited
            # Reduce concurrency by 20%
            new_concurrency = int(self.current_concurrency * 0.8)
            self.current_concurrency = max(new_concurrency, self.min_concurrency)
            logger.info(
                f"Rate limits detected ({rate_limit_rate:.1%}), reducing concurrency to {self.current_concurrency}",
                extra={"rate_limit_rate": rate_limit_rate, "new_concurrency": self.current_concurrency},
            )
        
        elif rate_limit_rate == 0.0 and self.current_concurrency < self.max_concurrency:
            # Increase concurrency by 10%
            new_concurrency = int(self.current_concurrency * 1.1)
            self.current_concurrency = min(new_concurrency, self.max_concurrency)
            logger.debug(
                f"No rate limits, increasing concurrency to {self.current_concurrency}",
                extra={"new_concurrency": self.current_concurrency},
            )
    
    async def batch_chat(
        self,
        queries: list[str],
        *,
        model: str | None = None,
        **kwargs: Any,
    ) -> list[LLMResponse | Exception]:
        """
        Batch chat with adaptive concurrency.
        
        Args:
            queries: List of queries
            model: Model to use
            **kwargs: Additional args
        
        Returns:
            List of responses
        """
        batcher = ConcurrentBatcher(max_concurrency=self.current_concurrency)
        results = await batcher.batch_chat(queries, model=model, return_exceptions=True, **kwargs)
        
        # Count rate limit errors (429)
        rate_limit_count = sum(
            1 for r in results
            if isinstance(r, Exception) and "429" in str(r)
        )
        rate_limit_rate = rate_limit_count / len(results) if results else 0.0
        
        # Adjust concurrency for next batch
        self._adjust_concurrency(rate_limit_rate)
        
        return results


# Convenience functions
async def batch_chat(
    queries: list[str],
    *,
    max_concurrency: int = 50,
    model: str | None = None,
    return_exceptions: bool = True,
    **kwargs: Any,
) -> list[LLMResponse | Exception]:
    """
    Convenience function for batch chat.
    
    Example:
        >>> from cost_optimization.batching import batch_chat
        >>> 
        >>> queries = ["Question 1?", "Question 2?", "Question 3?"]
        >>> responses = await batch_chat(queries, max_concurrency=10)
    """
    batcher = ConcurrentBatcher(max_concurrency=max_concurrency)
    return await batcher.batch_chat(
        queries=queries,
        model=model,
        return_exceptions=return_exceptions,
        **kwargs,
    )


async def batch_process(
    items: list[Any],
    process_fn: Callable[[Any], Any],
    max_concurrency: int = 50,
) -> list[Any]:
    """
    Generic batch processing with concurrency control.
    
    Args:
        items: Items to process
        process_fn: Async function to process each item
        max_concurrency: Max concurrent tasks
    
    Returns:
        List of results
    
    Example:
        >>> async def process_query(query: str) -> str:
        ...     response = await chat([{"role": "user", "content": query}])
        ...     return response.text
        >>> 
        >>> results = await batch_process(
        ...     items=["Q1", "Q2", "Q3"],
        ...     process_fn=process_query,
        ...     max_concurrency=10
        ... )
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def rate_limited_process(item: Any) -> Any:
        async with semaphore:
            return await process_fn(item)
    
    tasks = [rate_limited_process(item) for item in items]
    return await asyncio.gather(*tasks, return_exceptions=True)
