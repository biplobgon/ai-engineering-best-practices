"""
Model Comparison: Compare LLM models by cost, quality, and latency tradeoffs.

This script demonstrates:
1. Multi-dimensional model comparison
2. Finding optimal model for budget/quality constraints
3. Simulating costs with different routing strategies
4. Quality vs cost tradeoff visualization

Run: python model_comparison.py
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"  # Classification, extraction
    MEDIUM = "medium"  # Summarization, QA
    COMPLEX = "complex"  # Analysis, reasoning, code generation


@dataclass
class ModelCapabilities:
    """Model capabilities and characteristics."""
    name: str
    cost_per_1k_tokens: float  # Average cost (input + output)
    quality_score: int  # 1-100 scale
    speed_tokens_per_sec: int
    context_window: int
    best_for: List[str]  # Use cases


# Model database with capabilities
MODELS: Dict[str, ModelCapabilities] = {
    "gpt-4o": ModelCapabilities(
        name="GPT-4o",
        cost_per_1k_tokens=0.010,  # ($5 in + $15 out) / 2
        quality_score=95,
        speed_tokens_per_sec=50,
        context_window=128_000,
        best_for=["analysis", "reasoning", "code_generation"],
    ),
    "gpt-4o-mini": ModelCapabilities(
        name="GPT-4o-mini",
        cost_per_1k_tokens=0.000375,  # ($0.15 in + $0.60 out) / 2
        quality_score=85,
        speed_tokens_per_sec=100,
        context_window=128_000,
        best_for=["chat", "summarization", "qa"],
    ),
    "claude-3-5-sonnet": ModelCapabilities(
        name="Claude 3.5 Sonnet",
        cost_per_1k_tokens=0.009,
        quality_score=96,
        speed_tokens_per_sec=50,
        context_window=200_000,
        best_for=["analysis", "writing", "reasoning"],
    ),
    "claude-3-5-haiku": ModelCapabilities(
        name="Claude 3.5 Haiku",
        cost_per_1k_tokens=0.0024,
        quality_score=82,
        speed_tokens_per_sec=120,
        context_window=200_000,
        best_for=["classification", "extraction", "chat"],
    ),
    "gemini-1.5-flash": ModelCapabilities(
        name="Gemini 1.5 Flash",
        cost_per_1k_tokens=0.0007,
        quality_score=80,
        speed_tokens_per_sec=150,
        context_window=1_000_000,
        best_for=["long_context", "summarization"],
    ),
}


def compare_models(
    criteria: str = "cost",
    ascending: bool = True,
) -> List[Tuple[str, ModelCapabilities]]:
    """
    Compare models by specific criteria.
    
    Args:
        criteria: Sort criteria (cost, quality, speed, context)
        ascending: Sort order
        
    Returns:
        Sorted list of (model_id, capabilities)
    """
    sort_keys = {
        "cost": lambda x: x[1].cost_per_1k_tokens,
        "quality": lambda x: x[1].quality_score,
        "speed": lambda x: x[1].speed_tokens_per_sec,
        "context": lambda x: x[1].context_window,
    }
    
    if criteria not in sort_keys:
        raise ValueError(f"Invalid criteria: {criteria}. Choose from {list(sort_keys.keys())}")
    
    sorted_models = sorted(
        MODELS.items(),
        key=sort_keys[criteria],
        reverse=not ascending,
    )
    
    return sorted_models


def find_best_model(
    quality_threshold: int = 85,
    max_cost_per_1k: Optional[float] = None,
    min_speed: Optional[int] = None,
    min_context: Optional[int] = None,
) -> Optional[str]:
    """
    Find the cheapest model meeting quality and performance requirements.
    
    Args:
        quality_threshold: Minimum quality score (1-100)
        max_cost_per_1k: Maximum cost per 1K tokens
        min_speed: Minimum tokens per second
        min_context: Minimum context window
        
    Returns:
        Model ID or None if no model matches
    """
    candidates = []
    
    for model_id, caps in MODELS.items():
        # Check all constraints
        if caps.quality_score < quality_threshold:
            continue
        if max_cost_per_1k and caps.cost_per_1k_tokens > max_cost_per_1k:
            continue
        if min_speed and caps.speed_tokens_per_sec < min_speed:
            continue
        if min_context and caps.context_window < min_context:
            continue
        
        candidates.append((model_id, caps))
    
    if not candidates:
        return None
    
    # Return cheapest candidate
    best = min(candidates, key=lambda x: x[1].cost_per_1k_tokens)
    return best[0]


def calculate_efficiency_score(
    model_id: str,
    weight_cost: float = 0.4,
    weight_quality: float = 0.4,
    weight_speed: float = 0.2,
) -> float:
    """
    Calculate multi-dimensional efficiency score.
    
    Args:
        model_id: Model identifier
        weight_cost: Weight for cost (lower is better)
        weight_quality: Weight for quality (higher is better)
        weight_speed: Weight for speed (higher is better)
        
    Returns:
        Efficiency score (0-100, higher is better)
    """
    caps = MODELS[model_id]
    
    # Normalize metrics (0-1 scale)
    max_cost = max(m.cost_per_1k_tokens for m in MODELS.values())
    max_speed = max(m.speed_tokens_per_sec for m in MODELS.values())
    
    # Cost: lower is better (invert)
    cost_score = 1 - (caps.cost_per_1k_tokens / max_cost)
    
    # Quality: already 0-100, normalize to 0-1
    quality_score = caps.quality_score / 100
    
    # Speed: higher is better
    speed_score = caps.speed_tokens_per_sec / max_speed
    
    # Weighted sum
    efficiency = (
        cost_score * weight_cost +
        quality_score * weight_quality +
        speed_score * weight_speed
    ) * 100
    
    return efficiency


def simulate_routing_strategy(
    requests_per_day: int,
    task_distribution: Dict[TaskComplexity, float],
    avg_tokens_per_request: int = 1500,
) -> Dict[str, any]:
    """
    Simulate costs with intelligent routing strategy.
    
    Args:
        requests_per_day: Daily request volume
        task_distribution: Distribution of task complexities
        avg_tokens_per_request: Average tokens per request
        
    Returns:
        Cost simulation results
    """
    # Routing rules: complexity → model
    routing_rules = {
        TaskComplexity.SIMPLE: "claude-3-5-haiku",
        TaskComplexity.MEDIUM: "gpt-4o-mini",
        TaskComplexity.COMPLEX: "claude-3-5-sonnet",
    }
    
    # Calculate costs per complexity
    total_daily_cost = 0
    breakdown = {}
    
    for complexity, percentage in task_distribution.items():
        model_id = routing_rules[complexity]
        caps = MODELS[model_id]
        
        requests = requests_per_day * percentage
        tokens = requests * avg_tokens_per_request
        cost = (tokens / 1000) * caps.cost_per_1k_tokens
        
        breakdown[complexity.value] = {
            "model": caps.name,
            "requests": requests,
            "tokens": tokens,
            "daily_cost": cost,
            "monthly_cost": cost * 30,
        }
        
        total_daily_cost += cost
    
    # Compare to single-model strategy (GPT-4o for everything)
    single_model_cost = (
        requests_per_day * avg_tokens_per_request / 1000
    ) * MODELS["gpt-4o"].cost_per_1k_tokens
    
    savings = single_model_cost - total_daily_cost
    savings_pct = (savings / single_model_cost * 100) if single_model_cost > 0 else 0
    
    return {
        "routing_strategy": routing_rules,
        "breakdown": breakdown,
        "total_daily_cost": total_daily_cost,
        "total_monthly_cost": total_daily_cost * 30,
        "single_model_daily_cost": single_model_cost,
        "single_model_monthly_cost": single_model_cost * 30,
        "daily_savings": savings,
        "monthly_savings": savings * 30,
        "savings_percentage": savings_pct,
    }


def analyze_quality_cost_tradeoff() -> List[Dict[str, any]]:
    """
    Analyze quality vs cost tradeoff across models.
    
    Returns:
        List of tradeoff data points
    """
    tradeoffs = []
    
    for model_id, caps in MODELS.items():
        # Calculate cost per quality point
        cost_per_quality_point = caps.cost_per_1k_tokens / caps.quality_score
        
        # Calculate quality-adjusted cost (lower is better)
        quality_adjusted_cost = caps.cost_per_1k_tokens / (caps.quality_score / 100)
        
        tradeoffs.append({
            "model": caps.name,
            "model_id": model_id,
            "cost_per_1k": caps.cost_per_1k_tokens,
            "quality_score": caps.quality_score,
            "cost_per_quality_point": cost_per_quality_point,
            "quality_adjusted_cost": quality_adjusted_cost,
            "value_rating": "excellent" if quality_adjusted_cost < 0.005 else
                           "good" if quality_adjusted_cost < 0.010 else
                           "fair",
        })
    
    # Sort by quality-adjusted cost (best value first)
    tradeoffs.sort(key=lambda x: x["quality_adjusted_cost"])
    
    return tradeoffs


def main():
    """Run model comparison demos."""
    print("="*80)
    print("🔬 LLM MODEL COMPARISON")
    print("="*80)
    
    # Demo 1: Basic comparison
    print("\n" + "="*80)
    print("Demo 1: Model Comparison by Cost")
    print("="*80)
    
    cost_sorted = compare_models("cost", ascending=True)
    
    print(f"\n{'Model':<25} {'Cost/1K':>12} {'Quality':>10} {'Speed':>12} {'Context':>12}")
    print("-" * 80)
    
    for model_id, caps in cost_sorted:
        print(
            f"{caps.name:<25} "
            f"${caps.cost_per_1k_tokens:>11.6f} "
            f"{caps.quality_score:>9}/100 "
            f"{caps.speed_tokens_per_sec:>10}t/s "
            f"{caps.context_window:>10,}t"
        )
    
    # Demo 2: Find best model for constraints
    print("\n" + "="*80)
    print("Demo 2: Find Best Model for Constraints")
    print("="*80)
    
    scenarios = [
        {
            "name": "High quality, any cost",
            "quality_threshold": 95,
            "max_cost_per_1k": None,
        },
        {
            "name": "Good quality, budget-conscious",
            "quality_threshold": 85,
            "max_cost_per_1k": 0.001,
        },
        {
            "name": "Long context, fast",
            "quality_threshold": 80,
            "min_context": 500_000,
            "min_speed": 100,
        },
    ]
    
    for scenario in scenarios:
        best = find_best_model(**{k: v for k, v in scenario.items() if k != "name"})
        
        if best:
            caps = MODELS[best]
            print(f"\n{scenario['name']}:")
            print(f"  Best model: {caps.name}")
            print(f"  Cost: ${caps.cost_per_1k_tokens:.6f}/1K tokens")
            print(f"  Quality: {caps.quality_score}/100")
        else:
            print(f"\n{scenario['name']}:")
            print(f"  No model matches constraints")
    
    # Demo 3: Efficiency scores
    print("\n" + "="*80)
    print("Demo 3: Multi-dimensional Efficiency Scores")
    print("="*80)
    
    efficiency_scores = []
    for model_id in MODELS:
        score = calculate_efficiency_score(model_id)
        efficiency_scores.append((model_id, score))
    
    efficiency_scores.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Model':<25} {'Efficiency':>12} {'Best For':<40}")
    print("-" * 80)
    
    for model_id, score in efficiency_scores:
        caps = MODELS[model_id]
        best_for = ", ".join(caps.best_for[:2])
        print(f"{caps.name:<25} {score:>11.1f}/100 {best_for:<40}")
    
    # Demo 4: Routing strategy simulation
    print("\n" + "="*80)
    print("Demo 4: Intelligent Routing Strategy")
    print("="*80)
    
    # Typical task distribution
    task_dist = {
        TaskComplexity.SIMPLE: 0.50,  # 50% simple tasks
        TaskComplexity.MEDIUM: 0.35,  # 35% medium tasks
        TaskComplexity.COMPLEX: 0.15,  # 15% complex tasks
    }
    
    results = simulate_routing_strategy(
        requests_per_day=100_000,
        task_distribution=task_dist,
        avg_tokens_per_request=1500,
    )
    
    print(f"\nRouting strategy (100K requests/day):")
    print(f"\nTask breakdown:")
    
    for complexity, data in results["breakdown"].items():
        print(f"\n  {complexity.capitalize()} tasks ({task_dist[TaskComplexity[complexity.upper()]] * 100:.0f}%):")
        print(f"    Model: {data['model']}")
        print(f"    Requests: {data['requests']:,.0f}")
        print(f"    Daily cost: ${data['daily_cost']:.2f}")
        print(f"    Monthly cost: ${data['monthly_cost']:.2f}")
    
    print(f"\n{'Strategy':<30} {'Daily Cost':>15} {'Monthly Cost':>15}")
    print("-" * 65)
    print(f"{'Intelligent routing':<30} ${results['total_daily_cost']:>14.2f} ${results['total_monthly_cost']:>14.2f}")
    print(f"{'Single model (GPT-4o)':<30} ${results['single_model_daily_cost']:>14.2f} ${results['single_model_monthly_cost']:>14.2f}")
    print(f"{'Savings':<30} ${results['daily_savings']:>14.2f} ${results['monthly_savings']:>14.2f}")
    print(f"\nSavings: {results['savings_percentage']:.1f}%")
    
    # Demo 5: Quality vs Cost tradeoff
    print("\n" + "="*80)
    print("Demo 5: Quality vs Cost Tradeoff Analysis")
    print("="*80)
    
    tradeoffs = analyze_quality_cost_tradeoff()
    
    print(f"\n{'Model':<25} {'Quality':>10} {'Cost/1K':>12} {'Cost/Quality':>15} {'Value':>10}")
    print("-" * 80)
    
    for t in tradeoffs:
        print(
            f"{t['model']:<25} "
            f"{t['quality_score']:>9}/100 "
            f"${t['cost_per_1k']:>11.6f} "
            f"${t['cost_per_quality_point']:>14.8f} "
            f"{t['value_rating']:>10}"
        )
    
    # Demo 6: Use case recommendations
    print("\n" + "="*80)
    print("Demo 6: Use Case Recommendations")
    print("="*80)
    
    use_cases = {
        "Classification": {"quality": 80, "max_cost": 0.001},
        "Customer support chat": {"quality": 85, "max_cost": 0.002},
        "Document summarization": {"quality": 85, "min_context": 100_000},
        "Code generation": {"quality": 95, "max_cost": None},
        "Data analysis": {"quality": 95, "max_cost": None},
        "Simple QA": {"quality": 80, "max_cost": 0.0005},
    }
    
    print(f"\n{'Use Case':<30} {'Recommended Model':<25} {'Cost/1K':>12}")
    print("-" * 70)
    
    for use_case, constraints in use_cases.items():
        best = find_best_model(
            quality_threshold=constraints["quality"],
            max_cost_per_1k=constraints.get("max_cost"),
            min_context=constraints.get("min_context"),
        )
        
        if best:
            caps = MODELS[best]
            print(f"{use_case:<30} {caps.name:<25} ${caps.cost_per_1k_tokens:>11.6f}")
        else:
            print(f"{use_case:<30} {'No match':<25} {'N/A':>12}")
    
    print("\n" + "="*80)
    print("✅ Demo complete!")
    print("="*80)
    print("\nKey takeaways:")
    print("  • Different models excel at different tasks")
    print("  • Intelligent routing can save 60-80% on costs")
    print("  • Quality-adjusted cost is better metric than raw cost")
    print("  • Match model capabilities to task requirements")
    print("  • Simple tasks don't need the most powerful models")


if __name__ == "__main__":
    main()
