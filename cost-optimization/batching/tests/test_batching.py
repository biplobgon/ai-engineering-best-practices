"""
Tests for batching strategies.

Run with: pytest cost-optimization/batching/tests/
"""

import pytest
from unittest.mock import AsyncMock, patch
import asyncio

from cost_optimization.batching import (
    batch_chat,
    batch_embed,
    ConcurrentBatcher,
    AdaptiveBatcher,
    CoalescingCache,
)
from core.schemas import LLMResponse


@pytest.fixture
def mock_response():
    """Mock LLM response."""
    return LLMResponse(
        text="Response",
        tokens_in=10,
        tokens_out=5,
        usd_cost=0.0001,
        latency_ms=200,
        model="claude-3-5-haiku",
        cached=False,
        finish_reason="stop",
    )


class TestConcurrentBatcher:
    """Tests for concurrent batching."""
    
    @pytest.mark.asyncio
    async def test_batch_chat(self, mock_response):
        """Test basic batch chat."""
        queries = ["Q1", "Q2", "Q3"]
        
        with patch("cost_optimization.batching.concurrent_calls.chat", new=AsyncMock(return_value=mock_response)):
            responses = await batch_chat(queries, max_concurrency=2)
        
        assert len(responses) == 3
        assert all(isinstance(r, LLMResponse) for r in responses)
    
    @pytest.mark.asyncio
    async def test_return_exceptions(self, mock_response):
        """Test handling failures with return_exceptions."""
        queries = ["Q1", "Q2", "Q3"]
        
        # First fails, rest succeed
        mock_chat = AsyncMock(side_effect=[Exception("Error"), mock_response, mock_response])
        
        with patch("cost_optimization.batching.concurrent_calls.chat", new=mock_chat):
            responses = await batch_chat(queries, return_exceptions=True)
        
        assert len(responses) == 3
        assert isinstance(responses[0], Exception)
        assert isinstance(responses[1], LLMResponse)
        assert isinstance(responses[2], LLMResponse)
    
    @pytest.mark.asyncio
    async def test_concurrent_limit(self, mock_response):
        """Test concurrency limiting."""
        batcher = ConcurrentBatcher(max_concurrency=2)
        queries = ["Q1", "Q2", "Q3", "Q4"]
        
        with patch("cost_optimization.batching.concurrent_calls.chat", new=AsyncMock(return_value=mock_response)):
            responses = await batcher.batch_chat(queries)
        
        assert len(responses) == 4


class TestAdaptiveBatcher:
    """Tests for adaptive batching."""
    
    @pytest.mark.asyncio
    async def test_concurrency_reduction_on_rate_limit(self):
        """Test concurrency reduces on rate limits."""
        batcher = AdaptiveBatcher(initial_concurrency=50)
        
        # Simulate rate limit errors
        rate_limit_error = Exception("429 Rate Limit")
        mock_response = LLMResponse(
            text="Response",
            tokens_in=10,
            tokens_out=5,
            usd_cost=0.0001,
            latency_ms=200,
            model="test",
            cached=False,
            finish_reason="stop",
        )
        
        # 50% rate limited
        mock_chat = AsyncMock(side_effect=[rate_limit_error, mock_response] * 5)
        
        with patch("cost_optimization.batching.concurrent_calls.chat", new=mock_chat):
            await batcher.batch_chat(["Q"] * 10)
        
        # Concurrency should decrease
        assert batcher.current_concurrency < 50


class TestEmbedBatching:
    """Tests for embedding batching."""
    
    @pytest.mark.asyncio
    async def test_batch_embed(self):
        """Test batch embedding."""
        texts = [f"Text {i}" for i in range(250)]
        
        mock_embeddings = [[0.1] * 768 for _ in range(100)]  # Batch of 100
        
        with patch("cost_optimization.batching.embed_batching.embed", new=AsyncMock(return_value=mock_embeddings)) as mock_embed:
            embeddings = await batch_embed(texts, batch_size=100)
        
        # Should make 3 calls (250 / 100 = 3 batches)
        assert mock_embed.call_count == 3
        assert len(embeddings) == 250
    
    @pytest.mark.asyncio
    async def test_estimate_embedding_cost(self):
        """Test cost estimation."""
        from cost_optimization.batching.embed_batching import estimate_embedding_cost
        
        estimate = estimate_embedding_cost(
            num_texts=10000,
            avg_tokens_per_text=100,
            model="text-embedding-3-small"
        )
        
        assert estimate["num_texts"] == 10000
        assert estimate["total_tokens"] == 1_000_000
        assert estimate["usd_cost"] == 0.02  # $0.02 per 1M tokens
        assert estimate["api_calls"] == 100  # 10K / 100 batch size


class TestRequestCoalescing:
    """Tests for request coalescing."""
    
    @pytest.mark.asyncio
    async def test_coalescing_dedupes_requests(self):
        """Test that identical requests are coalesced."""
        cache = CoalescingCache()
        
        call_count = 0
        
        async def expensive_call():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate work
            return "result"
        
        # Make 10 identical requests concurrently
        tasks = [
            cache.get_or_compute("key1", expensive_call)
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Should only call once
        assert call_count == 1
        assert all(r == "result" for r in results)
    
    @pytest.mark.asyncio
    async def test_different_keys_not_coalesced(self):
        """Test that different keys are not coalesced."""
        cache = CoalescingCache()
        
        call_count = 0
        
        async def expensive_call():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"
        
        # Make requests with different keys
        r1 = await cache.get_or_compute("key1", expensive_call)
        r2 = await cache.get_or_compute("key2", expensive_call)
        
        assert call_count == 2
        assert r1 != r2


class TestPerformance:
    """Performance comparison tests."""
    
    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self, mock_response):
        """Verify parallel execution is faster."""
        queries = ["Q"] * 20
        
        # Mock with delay
        async def delayed_chat(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms delay
            return mock_response
        
        # Sequential
        start = asyncio.get_event_loop().time()
        with patch("cost_optimization.batching.concurrent_calls.chat", new=delayed_chat):
            for query in queries:
                await delayed_chat()
        sequential_time = asyncio.get_event_loop().time() - start
        
        # Parallel
        start = asyncio.get_event_loop().time()
        with patch("cost_optimization.batching.concurrent_calls.chat", new=delayed_chat):
            await batch_chat(queries, max_concurrency=10)
        parallel_time = asyncio.get_event_loop().time() - start
        
        # Parallel should be significantly faster
        assert parallel_time < sequential_time * 0.6  # At least 40% faster
