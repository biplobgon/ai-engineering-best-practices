"""
Tests for cost calculator functionality.
"""

import pytest
from fundamentals.fundamentals_02_tokens_and_cost.cost_calculator import (
    calculate_cost,
    estimate_monthly_cost,
    compare_models,
    calculate_cache_roi,
    MODEL_PRICING,
)
from fundamentals.fundamentals_02_tokens_and_cost.model_comparison import (
    compare_models as compare_models_caps,
    find_best_model,
    calculate_efficiency_score,
    simulate_routing_strategy,
    TaskComplexity,
)


class TestCostCalculator:
    """Tests for cost calculation functions."""
    
    def test_calculate_cost_basic(self):
        """Test basic cost calculation."""
        cost = calculate_cost(1000, 200, "gpt-4o-mini")
        
        assert "input_cost_usd" in cost
        assert "output_cost_usd" in cost
        assert "total_cost_usd" in cost
        assert cost["total_cost_usd"] > 0
        assert cost["output_cost_usd"] > cost["input_cost_usd"]  # Output more expensive
    
    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        cost = calculate_cost(0, 0, "gpt-4o-mini")
        
        assert cost["total_cost_usd"] == 0
        assert cost["input_cost_usd"] == 0
        assert cost["output_cost_usd"] == 0
    
    def test_calculate_cost_invalid_model(self):
        """Test cost calculation with invalid model."""
        with pytest.raises(ValueError, match="Unknown model"):
            calculate_cost(1000, 200, "invalid-model")
    
    def test_calculate_cost_latency(self):
        """Test latency calculation."""
        cost = calculate_cost(1000, 500, "gpt-4o-mini")
        
        assert "latency_seconds" in cost
        assert cost["latency_seconds"] > 0
        # 500 tokens at 100 tokens/sec = 5 seconds
        assert 4.0 <= cost["latency_seconds"] <= 6.0
    
    def test_estimate_monthly_cost_no_cache(self):
        """Test monthly cost estimation without caching."""
        estimate = estimate_monthly_cost(
            requests_per_day=1000,
            avg_input_tokens=500,
            avg_output_tokens=200,
            model="gpt-4o-mini",
            cache_hit_rate=0.0,
        )
        
        assert estimate["requests_per_day"] == 1000
        assert estimate["requests_per_month"] == 30000
        assert estimate["cache_hit_rate"] == 0.0
        assert estimate["monthly_cost_usd"] > 0
        assert estimate["monthly_savings_usd"] == 0  # No cache
    
    def test_estimate_monthly_cost_with_cache(self):
        """Test monthly cost estimation with caching."""
        estimate = estimate_monthly_cost(
            requests_per_day=1000,
            avg_input_tokens=500,
            avg_output_tokens=200,
            model="gpt-4o-mini",
            cache_hit_rate=0.8,
        )
        
        # Should be cheaper with cache
        no_cache = estimate_monthly_cost(
            requests_per_day=1000,
            avg_input_tokens=500,
            avg_output_tokens=200,
            model="gpt-4o-mini",
            cache_hit_rate=0.0,
        )
        
        assert estimate["monthly_cost_usd"] < no_cache["monthly_cost_usd"]
        assert estimate["monthly_savings_usd"] > 0
        assert estimate["savings_percentage"] > 0
    
    def test_compare_models(self):
        """Test model comparison."""
        comparisons = compare_models(1000, 500)
        
        assert len(comparisons) > 0
        # Should be sorted by cost (ascending)
        costs = [c["total_cost_usd"] for c in comparisons]
        assert costs == sorted(costs)
        
        # Check structure
        for comp in comparisons:
            assert "model" in comp
            assert "total_cost_usd" in comp
            assert "latency_seconds" in comp
    
    def test_compare_models_specific(self):
        """Test model comparison with specific models."""
        models = ["gpt-4o-mini", "claude-3-5-haiku"]
        comparisons = compare_models(1000, 500, models)
        
        assert len(comparisons) == 2
        model_names = [c["model"] for c in comparisons]
        assert set(model_names) == set(models)
    
    def test_calculate_cache_roi(self):
        """Test cache ROI calculation."""
        roi = calculate_cache_roi(
            requests_per_day=10000,
            avg_input_tokens=1000,
            avg_output_tokens=300,
            model="gpt-4o-mini",
            cache_hit_rate=0.8,
            cache_cost_monthly=50.0,
        )
        
        assert "monthly_llm_savings_usd" in roi
        assert "net_monthly_savings_usd" in roi
        assert "roi_percentage" in roi
        assert roi["monthly_llm_savings_usd"] > 0
        assert roi["roi_percentage"] > 0  # Should be positive ROI


class TestModelComparison:
    """Tests for model comparison functions."""
    
    def test_compare_models_by_cost(self):
        """Test comparing models by cost."""
        models = compare_models_caps("cost", ascending=True)
        
        assert len(models) > 0
        costs = [m[1].cost_per_1k_tokens for m in models]
        assert costs == sorted(costs)
    
    def test_compare_models_by_quality(self):
        """Test comparing models by quality."""
        models = compare_models_caps("quality", ascending=False)
        
        assert len(models) > 0
        qualities = [m[1].quality_score for m in models]
        assert qualities == sorted(qualities, reverse=True)
    
    def test_find_best_model_quality_only(self):
        """Test finding best model by quality threshold."""
        best = find_best_model(quality_threshold=90)
        
        assert best is not None
        # Should be a high-quality model
        assert best in ["gpt-4o", "claude-3-5-sonnet"]
    
    def test_find_best_model_budget(self):
        """Test finding best model with budget constraint."""
        best = find_best_model(quality_threshold=80, max_cost_per_1k=0.001)
        
        assert best is not None
        from fundamentals.fundamentals_02_tokens_and_cost.model_comparison import MODELS
        assert MODELS[best].cost_per_1k_tokens <= 0.001
        assert MODELS[best].quality_score >= 80
    
    def test_find_best_model_no_match(self):
        """Test finding best model with impossible constraints."""
        best = find_best_model(quality_threshold=99, max_cost_per_1k=0.0001)
        
        # Should return None (no model matches)
        assert best is None
    
    def test_calculate_efficiency_score(self):
        """Test efficiency score calculation."""
        score = calculate_efficiency_score("gpt-4o-mini")
        
        assert 0 <= score <= 100
        # GPT-4o-mini should have high efficiency (good balance)
        assert score > 50
    
    def test_efficiency_score_weights(self):
        """Test efficiency score with different weights."""
        # Cost-focused
        score_cost = calculate_efficiency_score(
            "gpt-4o-mini", weight_cost=0.8, weight_quality=0.1, weight_speed=0.1
        )
        
        # Quality-focused
        score_quality = calculate_efficiency_score(
            "gpt-4o", weight_cost=0.1, weight_quality=0.8, weight_speed=0.1
        )
        
        assert 0 <= score_cost <= 100
        assert 0 <= score_quality <= 100
    
    def test_simulate_routing_strategy(self):
        """Test routing strategy simulation."""
        task_dist = {
            TaskComplexity.SIMPLE: 0.5,
            TaskComplexity.MEDIUM: 0.3,
            TaskComplexity.COMPLEX: 0.2,
        }
        
        results = simulate_routing_strategy(
            requests_per_day=10000,
            task_distribution=task_dist,
        )
        
        assert "breakdown" in results
        assert "total_daily_cost" in results
        assert "savings_percentage" in results
        
        # Routing should be cheaper than single model
        assert results["total_daily_cost"] < results["single_model_daily_cost"]
        assert results["savings_percentage"] > 0
    
    def test_routing_strategy_breakdown(self):
        """Test routing strategy breakdown."""
        task_dist = {
            TaskComplexity.SIMPLE: 0.6,
            TaskComplexity.MEDIUM: 0.3,
            TaskComplexity.COMPLEX: 0.1,
        }
        
        results = simulate_routing_strategy(
            requests_per_day=5000,
            task_distribution=task_dist,
        )
        
        # Check all complexities in breakdown
        assert TaskComplexity.SIMPLE.value in results["breakdown"]
        assert TaskComplexity.MEDIUM.value in results["breakdown"]
        assert TaskComplexity.COMPLEX.value in results["breakdown"]
        
        # Verify request distribution
        simple_data = results["breakdown"][TaskComplexity.SIMPLE.value]
        assert simple_data["requests"] == 5000 * 0.6


class TestPricingData:
    """Tests for pricing data integrity."""
    
    def test_all_models_have_pricing(self):
        """Test that all models have complete pricing data."""
        for model_id, pricing in MODEL_PRICING.items():
            assert pricing.input_price_per_1m > 0
            assert pricing.output_price_per_1m > 0
            assert pricing.context_window > 0
            assert pricing.tokens_per_second > 0
    
    def test_output_more_expensive(self):
        """Test that output tokens are more expensive than input."""
        for model_id, pricing in MODEL_PRICING.items():
            assert pricing.output_price_per_1m >= pricing.input_price_per_1m
    
    def test_reasonable_price_ranges(self):
        """Test that prices are in reasonable ranges."""
        for model_id, pricing in MODEL_PRICING.items():
            # Input should be $0.10 to $10 per 1M tokens
            assert 0.1 <= pricing.input_price_per_1m <= 10.0
            # Output should be $0.50 to $30 per 1M tokens
            assert 0.5 <= pricing.output_price_per_1m <= 30.0
