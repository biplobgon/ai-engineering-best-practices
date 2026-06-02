"""
Cost Calculator: Calculate and estimate LLM costs across providers.

This script demonstrates:
1. Cost calculation for different models
2. Monthly cost estimation from usage patterns
3. Cost comparison across providers
4. ROI calculation for caching strategies

Run: python cost_calculator.py
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ModelPricing:
    """Model pricing configuration."""
    name: str
    input_price_per_1m: float  # USD per 1M input tokens
    output_price_per_1m: float  # USD per 1M output tokens
    context_window: int  # Max tokens
    tokens_per_second: int  # Generation speed


# Model pricing database (as of June 2026)
MODEL_PRICING: Dict[str, ModelPricing] = {
    "gpt-4o": ModelPricing(
        name="GPT-4o",
        input_price_per_1m=5.00,
        output_price_per_1m=15.00,
        context_window=128_000,
        tokens_per_second=50,
    ),
    "gpt-4o-mini": ModelPricing(
        name="GPT-4o-mini",
        input_price_per_1m=0.15,
        output_price_per_1m=0.60,
        context_window=128_000,
        tokens_per_second=100,
    ),
    "claude-3-5-sonnet": ModelPricing(
        name="Claude 3.5 Sonnet",
        input_price_per_1m=3.00,
        output_price_per_1m=15.00,
        context_window=200_000,
        tokens_per_second=50,
    ),
    "claude-3-5-haiku": ModelPricing(
        name="Claude 3.5 Haiku",
        input_price_per_1m=0.80,
        output_price_per_1m=4.00,
        context_window=200_000,
        tokens_per_second=120,
    ),
    "gemini-1.5-pro": ModelPricing(
        name="Gemini 1.5 Pro",
        input_price_per_1m=3.50,
        output_price_per_1m=10.50,
        context_window=2_000_000,
        tokens_per_second=30,
    ),
    "gemini-1.5-flash": ModelPricing(
        name="Gemini 1.5 Flash",
        input_price_per_1m=0.35,
        output_price_per_1m=1.05,
        context_window=1_000_000,
        tokens_per_second=150,
    ),
}


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4o-mini",
) -> Dict[str, float]:
    """
    Calculate cost for a single LLM call.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier
        
    Returns:
        Dictionary with cost breakdown
    """
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        raise ValueError(f"Unknown model: {model}. Available: {list(MODEL_PRICING.keys())}")
    
    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * pricing.input_price_per_1m
    output_cost = (output_tokens / 1_000_000) * pricing.output_price_per_1m
    total_cost = input_cost + output_cost
    
    # Calculate latency
    latency_seconds = output_tokens / pricing.tokens_per_second
    
    return {
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": total_cost,
        "latency_seconds": latency_seconds,
        "cost_per_second": total_cost / latency_seconds if latency_seconds > 0 else 0,
    }


def estimate_monthly_cost(
    requests_per_day: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    model: str = "gpt-4o-mini",
    cache_hit_rate: float = 0.0,
) -> Dict[str, float]:
    """
    Estimate monthly costs based on usage patterns.
    
    Args:
        requests_per_day: Average daily requests
        avg_input_tokens: Average input tokens per request
        avg_output_tokens: Average output tokens per request
        model: Model identifier
        cache_hit_rate: Percentage of requests served from cache (0.0-1.0)
        
    Returns:
        Monthly cost breakdown
    """
    # Calculate costs for uncached requests
    cost_per_request = calculate_cost(avg_input_tokens, avg_output_tokens, model)
    
    # Account for caching
    uncached_requests = requests_per_day * (1 - cache_hit_rate)
    cached_requests = requests_per_day * cache_hit_rate
    
    # Daily costs
    daily_cost_uncached = uncached_requests * cost_per_request["total_cost_usd"]
    daily_cost_cached = 0  # Assume cache hits are free
    daily_cost_total = daily_cost_uncached + daily_cost_cached
    
    # Monthly costs (30 days)
    monthly_cost = daily_cost_total * 30
    monthly_cost_no_cache = requests_per_day * cost_per_request["total_cost_usd"] * 30
    
    savings = monthly_cost_no_cache - monthly_cost
    savings_pct = (savings / monthly_cost_no_cache * 100) if monthly_cost_no_cache > 0 else 0
    
    return {
        "requests_per_day": requests_per_day,
        "requests_per_month": requests_per_day * 30,
        "cache_hit_rate": cache_hit_rate,
        "cost_per_request_usd": cost_per_request["total_cost_usd"],
        "daily_cost_usd": daily_cost_total,
        "monthly_cost_usd": monthly_cost,
        "monthly_cost_no_cache_usd": monthly_cost_no_cache,
        "monthly_savings_usd": savings,
        "savings_percentage": savings_pct,
    }


def compare_models(
    input_tokens: int,
    output_tokens: int,
    models: Optional[List[str]] = None,
) -> List[Dict[str, any]]:
    """
    Compare costs across different models.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        models: List of model identifiers (None = all models)
        
    Returns:
        List of cost comparisons sorted by total cost
    """
    if models is None:
        models = list(MODEL_PRICING.keys())
    
    results = []
    
    for model in models:
        try:
            cost = calculate_cost(input_tokens, output_tokens, model)
            pricing = MODEL_PRICING[model]
            
            results.append({
                "model": model,
                "name": pricing.name,
                "total_cost_usd": cost["total_cost_usd"],
                "input_cost_usd": cost["input_cost_usd"],
                "output_cost_usd": cost["output_cost_usd"],
                "latency_seconds": cost["latency_seconds"],
                "tokens_per_second": pricing.tokens_per_second,
                "context_window": pricing.context_window,
            })
        except Exception as e:
            print(f"Error calculating cost for {model}: {e}")
    
    # Sort by total cost (ascending)
    results.sort(key=lambda x: x["total_cost_usd"])
    
    return results


def calculate_cache_roi(
    requests_per_day: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    model: str,
    cache_hit_rate: float,
    cache_cost_monthly: float = 50.0,
) -> Dict[str, float]:
    """
    Calculate ROI for implementing caching.
    
    Args:
        requests_per_day: Daily request volume
        avg_input_tokens: Average input tokens
        avg_output_tokens: Average output tokens
        model: Model identifier
        cache_hit_rate: Expected cache hit rate (0.0-1.0)
        cache_cost_monthly: Monthly cost of cache infrastructure (Redis, etc.)
        
    Returns:
        ROI analysis
    """
    # Cost without caching
    no_cache = estimate_monthly_cost(
        requests_per_day, avg_input_tokens, avg_output_tokens, model, cache_hit_rate=0.0
    )
    
    # Cost with caching
    with_cache = estimate_monthly_cost(
        requests_per_day, avg_input_tokens, avg_output_tokens, model, cache_hit_rate
    )
    
    # Calculate ROI
    monthly_llm_savings = no_cache["monthly_cost_usd"] - with_cache["monthly_cost_usd"]
    net_savings = monthly_llm_savings - cache_cost_monthly
    roi_percentage = (net_savings / cache_cost_monthly * 100) if cache_cost_monthly > 0 else 0
    payback_months = cache_cost_monthly / monthly_llm_savings if monthly_llm_savings > 0 else float('inf')
    
    return {
        "monthly_cost_no_cache_usd": no_cache["monthly_cost_usd"],
        "monthly_cost_with_cache_usd": with_cache["monthly_cost_usd"],
        "monthly_llm_savings_usd": monthly_llm_savings,
        "cache_infrastructure_cost_usd": cache_cost_monthly,
        "net_monthly_savings_usd": net_savings,
        "roi_percentage": roi_percentage,
        "payback_months": payback_months,
    }


def main():
    """Run cost calculation demos."""
    print("="*80)
    print("💰 LLM COST CALCULATOR")
    print("="*80)
    
    # Demo 1: Single request cost
    print("\n" + "="*80)
    print("Demo 1: Single Request Cost Calculation")
    print("="*80)
    
    test_cases = [
        {"input": 1000, "output": 200, "model": "gpt-4o-mini", "desc": "Simple chat"},
        {"input": 5000, "output": 500, "model": "claude-3-5-haiku", "desc": "Document summary"},
        {"input": 10000, "output": 2000, "model": "gpt-4o", "desc": "Complex analysis"},
    ]
    
    for case in test_cases:
        cost = calculate_cost(case["input"], case["output"], case["model"])
        pricing = MODEL_PRICING[case["model"]]
        
        print(f"\n{case['desc']} ({pricing.name}):")
        print(f"  Input tokens: {case['input']:,}")
        print(f"  Output tokens: {case['output']:,}")
        print(f"  Input cost: ${cost['input_cost_usd']:.6f}")
        print(f"  Output cost: ${cost['output_cost_usd']:.6f}")
        print(f"  Total cost: ${cost['total_cost_usd']:.6f}")
        print(f"  Latency: {cost['latency_seconds']:.2f}s")
    
    # Demo 2: Model comparison
    print("\n" + "="*80)
    print("Demo 2: Model Cost Comparison")
    print("="*80)
    
    input_tokens = 2000
    output_tokens = 500
    
    print(f"\nComparing models for {input_tokens:,} input + {output_tokens:,} output tokens:\n")
    
    comparisons = compare_models(input_tokens, output_tokens)
    
    print(f"{'Model':<25} {'Cost':>10} {'Latency':>10} {'Speed':>12} {'Context':>12}")
    print("-" * 80)
    
    for comp in comparisons:
        print(
            f"{comp['name']:<25} "
            f"${comp['total_cost_usd']:>9.6f} "
            f"{comp['latency_seconds']:>9.1f}s "
            f"{comp['tokens_per_second']:>10}t/s "
            f"{comp['context_window']:>10,}t"
        )
    
    # Demo 3: Monthly cost estimation
    print("\n" + "="*80)
    print("Demo 3: Monthly Cost Estimation")
    print("="*80)
    
    scenarios = [
        {
            "name": "Small App (1K req/day)",
            "requests_per_day": 1_000,
            "avg_input": 500,
            "avg_output": 200,
            "model": "gpt-4o-mini",
        },
        {
            "name": "Medium App (10K req/day)",
            "requests_per_day": 10_000,
            "avg_input": 1000,
            "avg_output": 300,
            "model": "gpt-4o-mini",
        },
        {
            "name": "Large App (100K req/day)",
            "requests_per_day": 100_000,
            "avg_input": 2000,
            "avg_output": 500,
            "model": "claude-3-5-haiku",
        },
    ]
    
    for scenario in scenarios:
        estimate = estimate_monthly_cost(
            scenario["requests_per_day"],
            scenario["avg_input"],
            scenario["avg_output"],
            scenario["model"],
        )
        
        print(f"\n{scenario['name']}:")
        print(f"  Model: {MODEL_PRICING[scenario['model']].name}")
        print(f"  Requests/day: {estimate['requests_per_day']:,}")
        print(f"  Requests/month: {estimate['requests_per_month']:,}")
        print(f"  Cost/request: ${estimate['cost_per_request_usd']:.6f}")
        print(f"  Daily cost: ${estimate['daily_cost_usd']:.2f}")
        print(f"  Monthly cost: ${estimate['monthly_cost_usd']:.2f}")
    
    # Demo 4: Caching impact
    print("\n" + "="*80)
    print("Demo 4: Caching Impact on Costs")
    print("="*80)
    
    base_requests = 10_000
    base_input = 1000
    base_output = 300
    base_model = "gpt-4o-mini"
    
    cache_rates = [0.0, 0.5, 0.75, 0.9, 0.95]
    
    print(f"\nCost impact with different cache hit rates:")
    print(f"(10K req/day, {base_input} input + {base_output} output tokens, {MODEL_PRICING[base_model].name})\n")
    
    print(f"{'Cache Hit Rate':>15} {'Monthly Cost':>15} {'Savings':>15} {'Savings %':>12}")
    print("-" * 60)
    
    for rate in cache_rates:
        estimate = estimate_monthly_cost(
            base_requests, base_input, base_output, base_model, rate
        )
        
        print(
            f"{rate*100:>14.0f}% "
            f"${estimate['monthly_cost_usd']:>14.2f} "
            f"${estimate['monthly_savings_usd']:>14.2f} "
            f"{estimate['savings_percentage']:>11.1f}%"
        )
    
    # Demo 5: Cache ROI
    print("\n" + "="*80)
    print("Demo 5: Cache ROI Analysis")
    print("="*80)
    
    roi = calculate_cache_roi(
        requests_per_day=50_000,
        avg_input_tokens=1500,
        avg_output_tokens=400,
        model="claude-3-5-haiku",
        cache_hit_rate=0.85,
        cache_cost_monthly=100.0,
    )
    
    print("\nROI for implementing Redis cache:")
    print(f"  Monthly cost without cache: ${roi['monthly_cost_no_cache_usd']:.2f}")
    print(f"  Monthly cost with cache: ${roi['monthly_cost_with_cache_usd']:.2f}")
    print(f"  Monthly LLM savings: ${roi['monthly_llm_savings_usd']:.2f}")
    print(f"  Cache infrastructure cost: ${roi['cache_infrastructure_cost_usd']:.2f}")
    print(f"  Net monthly savings: ${roi['net_monthly_savings_usd']:.2f}")
    print(f"  ROI: {roi['roi_percentage']:.1f}%")
    print(f"  Payback period: {roi['payback_months']:.1f} months")
    
    # Demo 6: Cost optimization recommendations
    print("\n" + "="*80)
    print("Demo 6: Cost Optimization Recommendations")
    print("="*80)
    
    current_model = "gpt-4o"
    current_input = 3000
    current_output = 1000
    current_requests = 20_000
    
    current_cost = estimate_monthly_cost(
        current_requests, current_input, current_output, current_model
    )
    
    print(f"\nCurrent setup:")
    print(f"  Model: {MODEL_PRICING[current_model].name}")
    print(f"  Monthly cost: ${current_cost['monthly_cost_usd']:.2f}")
    
    print(f"\nOptimization options:")
    
    # Option 1: Switch to cheaper model
    cheaper_cost = estimate_monthly_cost(
        current_requests, current_input, current_output, "gpt-4o-mini"
    )
    savings_1 = current_cost['monthly_cost_usd'] - cheaper_cost['monthly_cost_usd']
    
    print(f"\n  1. Switch to GPT-4o-mini:")
    print(f"     Monthly cost: ${cheaper_cost['monthly_cost_usd']:.2f}")
    print(f"     Savings: ${savings_1:.2f} ({savings_1/current_cost['monthly_cost_usd']*100:.1f}%)")
    
    # Option 2: Reduce output tokens
    reduced_output_cost = estimate_monthly_cost(
        current_requests, current_input, 500, current_model
    )
    savings_2 = current_cost['monthly_cost_usd'] - reduced_output_cost['monthly_cost_usd']
    
    print(f"\n  2. Reduce output tokens (1000 → 500):")
    print(f"     Monthly cost: ${reduced_output_cost['monthly_cost_usd']:.2f}")
    print(f"     Savings: ${savings_2:.2f} ({savings_2/current_cost['monthly_cost_usd']*100:.1f}%)")
    
    # Option 3: Implement caching
    cached_cost = estimate_monthly_cost(
        current_requests, current_input, current_output, current_model, cache_hit_rate=0.8
    )
    savings_3 = current_cost['monthly_cost_usd'] - cached_cost['monthly_cost_usd']
    
    print(f"\n  3. Implement caching (80% hit rate):")
    print(f"     Monthly cost: ${cached_cost['monthly_cost_usd']:.2f}")
    print(f"     Savings: ${savings_3:.2f} ({savings_3/current_cost['monthly_cost_usd']*100:.1f}%)")
    
    print("\n" + "="*80)
    print("✅ Demo complete!")
    print("="*80)
    print("\nKey takeaways:")
    print("  • Output tokens are 3-10× more expensive than input")
    print("  • Model selection can reduce costs by 30-50×")
    print("  • Caching can reduce costs by 80-95%")
    print("  • Monitor costs per request, user, and endpoint")
    print("  • Set hard budget limits to prevent overruns")


if __name__ == "__main__":
    main()
