"""
Sampling Strategies: Different parameter combinations for common tasks.

This script demonstrates:
1. Pre-configured strategies for different use cases
2. A/B testing different sampling parameters
3. Adaptive sampling based on task complexity
4. Performance metrics for each strategy

Run: python sampling_strategies.py
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

from core.llm import chat
from core.config import get_settings


class TaskType(Enum):
    """Common task types."""
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    QA = "qa"
    CHAT = "chat"
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"


@dataclass
class SamplingStrategy:
    """Sampling parameter configuration."""
    name: str
    temperature: float
    max_tokens: int
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    description: str = ""


# Pre-configured strategies for common tasks
STRATEGIES: Dict[TaskType, SamplingStrategy] = {
    TaskType.CLASSIFICATION: SamplingStrategy(
        name="Classification",
        temperature=0.0,
        max_tokens=10,
        top_p=0.1,
        description="Deterministic, very short, highly focused",
    ),
    TaskType.EXTRACTION: SamplingStrategy(
        name="Extraction",
        temperature=0.0,
        max_tokens=100,
        top_p=0.1,
        stop=["\n\n"],
        description="Deterministic, bounded output",
    ),
    TaskType.SUMMARIZATION: SamplingStrategy(
        name="Summarization",
        temperature=0.3,
        max_tokens=300,
        top_p=0.9,
        description="Low creativity, controlled length",
    ),
    TaskType.QA: SamplingStrategy(
        name="Question Answering",
        temperature=0.2,
        max_tokens=200,
        top_p=0.9,
        description="Mostly deterministic, concise answers",
    ),
    TaskType.CHAT: SamplingStrategy(
        name="General Chat",
        temperature=0.7,
        max_tokens=500,
        top_p=0.9,
        frequency_penalty=0.3,
        description="Balanced creativity, avoid repetition",
    ),
    TaskType.CREATIVE_WRITING: SamplingStrategy(
        name="Creative Writing",
        temperature=1.0,
        max_tokens=2000,
        top_p=0.95,
        frequency_penalty=0.5,
        presence_penalty=0.5,
        description="High creativity, diverse vocabulary",
    ),
    TaskType.CODE_GENERATION: SamplingStrategy(
        name="Code Generation",
        temperature=0.2,
        max_tokens=1000,
        top_p=0.95,
        stop=["```\n\n", "# End"],
        description="Low creativity for correctness",
    ),
    TaskType.ANALYSIS: SamplingStrategy(
        name="Analysis",
        temperature=0.4,
        max_tokens=1000,
        top_p=0.9,
        frequency_penalty=0.2,
        description="Balanced, avoid repetition",
    ),
}


async def run_with_strategy(
    prompt: str,
    strategy: SamplingStrategy,
    model: str = "gpt-4o-mini",
) -> Dict[str, any]:
    """
    Run prompt with a specific sampling strategy.
    
    Args:
        prompt: Input prompt
        strategy: Sampling strategy to use
        model: Model identifier
        
    Returns:
        Result dictionary with response and metrics
    """
    try:
        result = await chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=strategy.temperature,
            max_tokens=strategy.max_tokens,
            top_p=strategy.top_p,
            frequency_penalty=strategy.frequency_penalty,
            presence_penalty=strategy.presence_penalty,
            stop=strategy.stop,
            cache=False,
        )
        
        return {
            "success": True,
            "text": result.text,
            "tokens_out": result.tokens_out,
            "cost_usd": result.usd_cost,
            "latency_ms": result.latency_ms,
            "strategy": strategy.name,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "strategy": strategy.name,
        }


async def ab_test_strategies(
    prompt: str,
    strategy_a: SamplingStrategy,
    strategy_b: SamplingStrategy,
    num_samples: int = 3,
) -> Dict[str, any]:
    """
    A/B test two different sampling strategies.
    
    Args:
        prompt: Input prompt
        strategy_a: First strategy
        strategy_b: Second strategy
        num_samples: Number of samples per strategy
        
    Returns:
        Comparison results
    """
    results_a = []
    results_b = []
    
    # Generate samples for strategy A
    for _ in range(num_samples):
        result = await run_with_strategy(prompt, strategy_a)
        if result["success"]:
            results_a.append(result)
    
    # Generate samples for strategy B
    for _ in range(num_samples):
        result = await run_with_strategy(prompt, strategy_b)
        if result["success"]:
            results_b.append(result)
    
    # Calculate metrics
    def calc_avg(results, key):
        values = [r[key] for r in results if key in r]
        return sum(values) / len(values) if values else 0
    
    return {
        "strategy_a": {
            "name": strategy_a.name,
            "samples": [r["text"] for r in results_a],
            "avg_tokens": calc_avg(results_a, "tokens_out"),
            "avg_cost": calc_avg(results_a, "cost_usd"),
            "avg_latency": calc_avg(results_a, "latency_ms"),
        },
        "strategy_b": {
            "name": strategy_b.name,
            "samples": [r["text"] for r in results_b],
            "avg_tokens": calc_avg(results_b, "tokens_out"),
            "avg_cost": calc_avg(results_b, "cost_usd"),
            "avg_latency": calc_avg(results_b, "latency_ms"),
        },
    }


def get_adaptive_strategy(
    task_type: TaskType,
    complexity: str = "medium",
    budget: str = "normal",
) -> SamplingStrategy:
    """
    Get adaptive strategy based on task and constraints.
    
    Args:
        task_type: Type of task
        complexity: Task complexity (simple, medium, complex)
        budget: Budget constraint (low, normal, high)
        
    Returns:
        Adapted sampling strategy
    """
    # Start with base strategy
    base = STRATEGIES[task_type]
    
    # Create a copy
    strategy = SamplingStrategy(
        name=f"{base.name} (adapted)",
        temperature=base.temperature,
        max_tokens=base.max_tokens,
        top_p=base.top_p,
        frequency_penalty=base.frequency_penalty,
        presence_penalty=base.presence_penalty,
        stop=base.stop,
    )
    
    # Adjust for complexity
    if complexity == "simple":
        strategy.temperature = max(0.0, strategy.temperature - 0.2)
        strategy.max_tokens = int(strategy.max_tokens * 0.5)
    elif complexity == "complex":
        strategy.temperature = min(1.0, strategy.temperature + 0.2)
        strategy.max_tokens = int(strategy.max_tokens * 1.5)
    
    # Adjust for budget
    if budget == "low":
        strategy.max_tokens = min(strategy.max_tokens, 200)
    elif budget == "high":
        strategy.max_tokens = int(strategy.max_tokens * 2)
    
    return strategy


async def demo_predefined_strategies():
    """Demo: Show predefined strategies for different tasks."""
    print("="*90)
    print("DEMO 1: Predefined Sampling Strategies")
    print("="*90)
    
    print(f"\n{'Task Type':<25} {'Temp':>6} {'Max Tok':>10} {'Top-p':>8} {'Freq Pen':>10} {'Pres Pen':>10}")
    print("-" * 90)
    
    for task_type, strategy in STRATEGIES.items():
        print(
            f"{strategy.name:<25} "
            f"{strategy.temperature:>6.1f} "
            f"{strategy.max_tokens:>10} "
            f"{strategy.top_p:>8.2f} "
            f"{strategy.frequency_penalty:>10.1f} "
            f"{strategy.presence_penalty:>10.1f}"
        )
        print(f"  → {strategy.description}")


async def demo_task_examples():
    """Demo: Run examples with appropriate strategies."""
    print("\n" + "="*90)
    print("DEMO 2: Task Examples with Optimal Strategies")
    print("="*90)
    
    settings = get_settings()
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        print("\n⚠️  Skipping live examples (no API keys found)")
        return
    
    examples = {
        TaskType.CLASSIFICATION: "Classify this sentiment: 'I absolutely love this product!'",
        TaskType.SUMMARIZATION: "Summarize: Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
        TaskType.CHAT: "What's the best way to learn programming?",
    }
    
    for task_type, prompt in examples.items():
        strategy = STRATEGIES[task_type]
        print(f"\n{strategy.name}:")
        print(f"  Prompt: {prompt[:70]}...")
        print(f"  Strategy: temp={strategy.temperature}, max_tokens={strategy.max_tokens}")
        
        result = await run_with_strategy(prompt, strategy)
        
        if result["success"]:
            print(f"  Response: {result['text'][:150]}...")
            print(f"  Tokens: {result['tokens_out']}, Cost: ${result['cost_usd']:.6f}, Latency: {result['latency_ms']:.0f}ms")


async def demo_ab_testing():
    """Demo: A/B test different strategies."""
    print("\n" + "="*90)
    print("DEMO 3: A/B Testing Strategies")
    print("="*90)
    
    settings = get_settings()
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        print("\n⚠️  Skipping A/B test (no API keys found)")
        return
    
    prompt = "Write a creative tagline for a coffee shop:"
    
    # Strategy A: Conservative
    strategy_a = SamplingStrategy(
        name="Conservative",
        temperature=0.5,
        max_tokens=50,
        top_p=0.8,
    )
    
    # Strategy B: Creative
    strategy_b = SamplingStrategy(
        name="Creative",
        temperature=1.0,
        max_tokens=50,
        top_p=0.95,
    )
    
    print(f"\nPrompt: '{prompt}'")
    print("\nTesting two strategies:")
    print(f"  A: {strategy_a.name} (temp={strategy_a.temperature})")
    print(f"  B: {strategy_b.name} (temp={strategy_b.temperature})")
    
    results = await ab_test_strategies(prompt, strategy_a, strategy_b, num_samples=3)
    
    print(f"\n{'-'*90}")
    print(f"Strategy A ({results['strategy_a']['name']}):")
    for i, sample in enumerate(results['strategy_a']['samples'], 1):
        print(f"  {i}. {sample}")
    print(f"  Avg tokens: {results['strategy_a']['avg_tokens']:.1f}")
    print(f"  Avg cost: ${results['strategy_a']['avg_cost']:.6f}")
    
    print(f"\n{'-'*90}")
    print(f"Strategy B ({results['strategy_b']['name']}):")
    for i, sample in enumerate(results['strategy_b']['samples'], 1):
        print(f"  {i}. {sample}")
    print(f"  Avg tokens: {results['strategy_b']['avg_tokens']:.1f}")
    print(f"  Avg cost: ${results['strategy_b']['avg_cost']:.6f}")


async def demo_adaptive_strategies():
    """Demo: Adaptive strategies based on constraints."""
    print("\n" + "="*90)
    print("DEMO 4: Adaptive Sampling Strategies")
    print("="*90)
    
    base_task = TaskType.CHAT
    
    scenarios = [
        {"complexity": "simple", "budget": "low"},
        {"complexity": "medium", "budget": "normal"},
        {"complexity": "complex", "budget": "high"},
    ]
    
    print(f"\nBase task: {STRATEGIES[base_task].name}")
    print(f"Base params: temp={STRATEGIES[base_task].temperature}, max_tokens={STRATEGIES[base_task].max_tokens}")
    
    print(f"\n{'Scenario':<30} {'Temp':>8} {'Max Tokens':>12} {'Adaptation':>25}")
    print("-" * 90)
    
    for scenario in scenarios:
        strategy = get_adaptive_strategy(base_task, **scenario)
        adaptation = f"{scenario['complexity']}/{scenario['budget']}"
        
        print(
            f"{strategy.name:<30} "
            f"{strategy.temperature:>8.1f} "
            f"{strategy.max_tokens:>12} "
            f"{adaptation:>25}"
        )


async def demo_parameter_interaction():
    """Demo: How parameters interact."""
    print("\n" + "="*90)
    print("DEMO 5: Parameter Interactions")
    print("="*90)
    
    print("\nCommon parameter combinations:\n")
    
    combinations = [
        {
            "name": "Deterministic (classification)",
            "params": {"temperature": 0.0, "top_p": 0.1, "max_tokens": 10},
            "effect": "Single, consistent output",
        },
        {
            "name": "Balanced (general chat)",
            "params": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 300},
            "effect": "Moderate variety, natural",
        },
        {
            "name": "Creative (writing)",
            "params": {"temperature": 1.0, "top_p": 0.95, "max_tokens": 1000},
            "effect": "High diversity, unique outputs",
        },
        {
            "name": "Focused creativity",
            "params": {"temperature": 1.0, "top_p": 0.5, "max_tokens": 500},
            "effect": "Creative but constrained vocabulary",
        },
    ]
    
    for combo in combinations:
        print(f"{combo['name']}:")
        params = combo['params']
        print(f"  Parameters: temp={params['temperature']}, top_p={params['top_p']}, max_tokens={params['max_tokens']}")
        print(f"  Effect: {combo['effect']}\n")


async def main():
    """Run all sampling strategy demos."""
    print("="*90)
    print("⚙️  SAMPLING STRATEGIES DEMO")
    print("="*90)
    
    await demo_predefined_strategies()
    await demo_task_examples()
    await demo_ab_testing()
    await demo_adaptive_strategies()
    await demo_parameter_interaction()
    
    print("\n" + "="*90)
    print("✅ Demo complete!")
    print("="*90)
    print("\nKey takeaways:")
    print("  • Match sampling strategy to task type")
    print("  • Classification/extraction: temp=0.0, low max_tokens")
    print("  • Creative tasks: temp=0.8-1.0, high max_tokens")
    print("  • Balanced tasks: temp=0.5-0.7, moderate max_tokens")
    print("  • Use frequency/presence penalties to reduce repetition")
    print("  • A/B test strategies to find optimal configuration")
    print("  • Adapt parameters based on complexity and budget")


if __name__ == "__main__":
    asyncio.run(main())
