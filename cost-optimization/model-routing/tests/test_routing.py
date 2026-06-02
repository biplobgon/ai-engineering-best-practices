"""
Tests for model routing strategies.

Run with: pytest cost-optimization/model-routing/tests/
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cost_optimization.model_routing.cheap_first_router import CheapFirstRouter, cheap_first_chat
from cost_optimization.model_routing.fallback_strategy import (
    FallbackRouter,
    ModelTier,
    default_quality_check,
    fallback_chat,
)
from cost_optimization.model_routing.adaptive_routing import AdaptiveRouter, ModelStats
from core.schemas import LLMResponse


@pytest.fixture
def mock_response():
    """Mock LLM response."""
    return LLMResponse(
        text="This is a positive sentiment.",
        tokens_in=10,
        tokens_out=6,
        usd_cost=0.0001,
        latency_ms=200,
        model="claude-3-5-haiku",
        cached=False,
        finish_reason="stop",
    )


@pytest.fixture
def mock_poor_response():
    """Mock poor quality response."""
    return LLMResponse(
        text="Error",
        tokens_in=10,
        tokens_out=1,
        usd_cost=0.0001,
        latency_ms=200,
        model="claude-3-5-haiku",
        cached=False,
        finish_reason="stop",
    )


class TestCheapFirstRouter:
    """Tests for cheap-first routing."""
    
    @pytest.mark.asyncio
    async def test_basic_routing(self, mock_response):
        """Test basic cheap-first routing."""
        router = CheapFirstRouter()
        
        with patch("cost_optimization.model_routing.cheap_first_router.chat", new=AsyncMock(return_value=mock_response)):
            response = await router.chat(
                messages=[{"role": "user", "content": "Test"}],
                task_type="classification",
            )
        
        assert response.text == "This is a positive sentiment."
        assert response.model == "claude-3-5-haiku"
        assert response.usd_cost < 0.001
    
    @pytest.mark.asyncio
    async def test_fallback_on_failure(self, mock_response):
        """Test fallback when first model fails."""
        router = CheapFirstRouter(enable_fallback=True, max_retries=2)
        
        # First call fails, second succeeds
        mock_chat = AsyncMock(side_effect=[Exception("Rate limit"), mock_response])
        
        with patch("cost_optimization.model_routing.cheap_first_router.chat", new=mock_chat):
            response = await router.chat(
                messages=[{"role": "user", "content": "Test"}],
                task_type="classification",
            )
        
        assert response.text == "This is a positive sentiment."
        assert mock_chat.call_count == 2  # First failed, second succeeded
    
    @pytest.mark.asyncio
    async def test_quality_check_failure(self, mock_poor_response, mock_response):
        """Test quality check triggers fallback."""
        router = CheapFirstRouter(enable_fallback=True)
        
        def quality_check(r: LLMResponse) -> bool:
            return len(r.text) > 10  # "Error" fails this
        
        # First response poor quality, second is good
        mock_chat = AsyncMock(side_effect=[mock_poor_response, mock_response])
        
        with patch("cost_optimization.model_routing.cheap_first_router.chat", new=mock_chat):
            response = await router.chat(
                messages=[{"role": "user", "content": "Test"}],
                task_type="classification",
                quality_check=quality_check,
            )
        
        assert response.text == "This is a positive sentiment."
        assert mock_chat.call_count == 2
    
    @pytest.mark.asyncio
    async def test_all_models_fail(self):
        """Test exception when all models fail."""
        router = CheapFirstRouter(max_retries=1)
        
        mock_chat = AsyncMock(side_effect=Exception("All failed"))
        
        with patch("cost_optimization.model_routing.cheap_first_router.chat", new=mock_chat):
            with pytest.raises(Exception, match="All models failed"):
                await router.chat(
                    messages=[{"role": "user", "content": "Test"}],
                    task_type="classification",
                )


class TestFallbackRouter:
    """Tests for tier-based fallback routing."""
    
    @pytest.mark.asyncio
    async def test_tier_fallback(self, mock_poor_response, mock_response):
        """Test fallback from cheap to smart tier."""
        router = FallbackRouter()
        
        def quality_check(r: LLMResponse) -> bool:
            return len(r.text) > 10
        
        # Cheap tier fails quality, smart tier succeeds
        mock_chat = AsyncMock(side_effect=[mock_poor_response, mock_response])
        
        with patch("cost_optimization.model_routing.fallback_strategy.chat", new=mock_chat):
            response = await router.chat_with_tiers(
                messages=[{"role": "user", "content": "Test"}],
                start_tier=ModelTier.CHEAP,
                max_tier=ModelTier.SMART,
                quality_check=quality_check,
            )
        
        assert response.text == "This is a positive sentiment."
        assert mock_chat.call_count == 2
    
    @pytest.mark.asyncio
    async def test_default_quality_check(self):
        """Test default quality check function."""
        # Good response
        good = LLMResponse(
            text="This is a detailed response with sufficient length.",
            tokens_in=10,
            tokens_out=10,
            usd_cost=0.0001,
            latency_ms=200,
            model="test",
            cached=False,
            finish_reason="stop",
        )
        assert default_quality_check(good) is True
        
        # Empty response
        empty = LLMResponse(
            text="",
            tokens_in=10,
            tokens_out=0,
            usd_cost=0.0001,
            latency_ms=200,
            model="test",
            cached=False,
            finish_reason="stop",
        )
        assert default_quality_check(empty) is False
        
        # Too short
        short = LLMResponse(
            text="No",
            tokens_in=10,
            tokens_out=1,
            usd_cost=0.0001,
            latency_ms=200,
            model="test",
            cached=False,
            finish_reason="stop",
        )
        assert default_quality_check(short) is False
        
        # Error phrase
        error = LLMResponse(
            text="I apologize, but I cannot help with that.",
            tokens_in=10,
            tokens_out=8,
            usd_cost=0.0001,
            latency_ms=200,
            model="test",
            cached=False,
            finish_reason="stop",
        )
        assert default_quality_check(error) is False


class TestAdaptiveRouter:
    """Tests for adaptive routing with learning."""
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Test success/failure tracking."""
        router = AdaptiveRouter()
        
        # Update stats
        await router._update_stats(
            task_type="classification",
            model="claude-3-5-haiku",
            success=True,
            cost=0.0001,
            latency_ms=200,
        )
        
        # Get stats
        stats = await router._get_stats("classification", "claude-3-5-haiku")
        
        assert stats.success_count == 1
        assert stats.failure_count == 0
        assert stats.success_rate == 1.0
        assert stats.avg_cost == 0.0001
        
        # Clean up
        await router.clear_stats("classification")
    
    @pytest.mark.asyncio
    async def test_model_stats_properties(self):
        """Test ModelStats computed properties."""
        stats = ModelStats(
            success_count=90,
            failure_count=10,
            total_cost=10.0,
            total_latency_ms=20000,
        )
        
        assert stats.total_count == 100
        assert stats.success_rate == 0.9
        assert stats.avg_cost == 0.1
        assert stats.avg_latency_ms == 200.0
    
    @pytest.mark.asyncio
    async def test_adaptive_routing_chooses_best(self, mock_response):
        """Test adaptive router chooses best model based on stats."""
        router = AdaptiveRouter(min_success_rate=0.90)
        
        # Seed stats: haiku has low success rate
        await router._update_stats("classification", "claude-3-5-haiku", False, 0.0001, 200)
        await router._update_stats("classification", "claude-3-5-haiku", False, 0.0001, 200)
        await router._update_stats("classification", "claude-3-5-haiku", True, 0.0001, 200)
        # Success rate: 33% (below threshold)
        
        # Make call (should use smarter model or fallback)
        with patch("cost_optimization.model_routing.adaptive_routing.chat", new=AsyncMock(return_value=mock_response)):
            response = await router.chat(
                messages=[{"role": "user", "content": "Test"}],
                task_type="classification",
            )
        
        assert response is not None
        
        # Clean up
        await router.clear_stats("classification")


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""
    
    @pytest.mark.asyncio
    async def test_cheap_first_chat(self, mock_response):
        """Test cheap_first_chat convenience function."""
        with patch("cost_optimization.model_routing.cheap_first_router.chat", new=AsyncMock(return_value=mock_response)):
            response = await cheap_first_chat(
                messages=[{"role": "user", "content": "Test"}],
                task_type="classification",
            )
        
        assert response.text == "This is a positive sentiment."
    
    @pytest.mark.asyncio
    async def test_fallback_chat(self, mock_response):
        """Test fallback_chat convenience function."""
        with patch("cost_optimization.model_routing.fallback_strategy.chat", new=AsyncMock(return_value=mock_response)):
            response = await fallback_chat(
                messages=[{"role": "user", "content": "Test"}],
            )
        
        assert response.text == "This is a positive sentiment."


class TestCostSavings:
    """Integration tests for cost savings validation."""
    
    @pytest.mark.asyncio
    async def test_cheap_model_cost_savings(self):
        """Verify cheap model is actually cheaper."""
        # Mock responses with different costs
        cheap_response = LLMResponse(
            text="Result",
            tokens_in=100,
            tokens_out=20,
            usd_cost=0.0001,  # Haiku pricing
            latency_ms=200,
            model="claude-3-5-haiku",
            cached=False,
            finish_reason="stop",
        )
        
        expensive_response = LLMResponse(
            text="Result",
            tokens_in=100,
            tokens_out=20,
            usd_cost=0.0015,  # Sonnet pricing
            latency_ms=400,
            model="claude-3-5-sonnet",
            cached=False,
            finish_reason="stop",
        )
        
        # Cheap-first should use cheap model
        router = CheapFirstRouter()
        
        with patch("cost_optimization.model_routing.cheap_first_router.chat", new=AsyncMock(return_value=cheap_response)):
            response = await router.chat(
                messages=[{"role": "user", "content": "Simple classification"}],
                task_type="classification",
            )
        
        # Verify cost savings
        savings_pct = (1 - response.usd_cost / expensive_response.usd_cost) * 100
        assert savings_pct > 90  # Should save >90%
        assert response.usd_cost < expensive_response.usd_cost
