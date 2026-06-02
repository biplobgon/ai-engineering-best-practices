"""
Temperature Demo: Interactive exploration of temperature effects on LLM outputs.

This script demonstrates:
1. How temperature affects output randomness
2. Comparing outputs at different temperatures
3. Measuring output diversity
4. Finding optimal temperature for tasks

Run: python temperature_demo.py

Note: Requires API keys set in environment or .env file.
"""

import asyncio
import statistics
from typing import List, Dict
from collections import Counter

from core.llm import chat
from core.config import get_settings


async def generate_at_temperature(
    prompt: str,
    temperature: float,
    model: str = "gpt-4o-mini",
    num_samples: int = 1,
) -> List[str]:
    """
    Generate responses at a specific temperature.
    
    Args:
        prompt: Input prompt
        temperature: Sampling temperature (0.0 to 2.0)
        model: Model identifier
        num_samples: Number of responses to generate
        
    Returns:
        List of generated responses
    """
    responses = []
    
    for _ in range(num_samples):
        try:
            result = await chat(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=temperature,
                max_tokens=100,
                cache=False,  # Disable cache to get fresh responses
            )
            responses.append(result.text.strip())
        except Exception as e:
            print(f"Error generating response: {e}")
            responses.append(f"[Error: {e}]")
    
    return responses


def calculate_diversity(responses: List[str]) -> Dict[str, float]:
    """
    Calculate diversity metrics for a set of responses.
    
    Args:
        responses: List of generated responses
        
    Returns:
        Dictionary with diversity metrics
    """
    if not responses:
        return {"unique_ratio": 0.0, "avg_length": 0, "length_variance": 0}
    
    # Unique responses ratio
    unique_count = len(set(responses))
    unique_ratio = unique_count / len(responses)
    
    # Length statistics
    lengths = [len(r) for r in responses]
    avg_length = statistics.mean(lengths)
    length_variance = statistics.variance(lengths) if len(lengths) > 1 else 0
    
    # Token-level diversity (first 5 tokens)
    first_tokens = [r.split()[:5] if r.split() else [] for r in responses]
    first_token_variety = len(set(tuple(tokens) for tokens in first_tokens))
    
    return {
        "unique_ratio": unique_ratio,
        "unique_count": unique_count,
        "total_count": len(responses),
        "avg_length": avg_length,
        "length_variance": length_variance,
        "first_token_variety": first_token_variety,
    }


async def compare_temperatures(
    prompt: str,
    temperatures: List[float],
    samples_per_temp: int = 5,
) -> Dict[float, Dict]:
    """
    Compare outputs across different temperatures.
    
    Args:
        prompt: Input prompt
        temperatures: List of temperatures to test
        samples_per_temp: Number of samples per temperature
        
    Returns:
        Results for each temperature
    """
    results = {}
    
    for temp in temperatures:
        print(f"\nGenerating {samples_per_temp} samples at temperature={temp}...")
        
        responses = await generate_at_temperature(
            prompt, temp, num_samples=samples_per_temp
        )
        
        diversity = calculate_diversity(responses)
        
        results[temp] = {
            "responses": responses,
            "diversity": diversity,
        }
    
    return results


def print_comparison_table(results: Dict[float, Dict]) -> None:
    """Print formatted comparison table."""
    print("\n" + "="*90)
    print("TEMPERATURE COMPARISON")
    print("="*90)
    
    print(f"\n{'Temp':>6} {'Unique %':>10} {'Avg Len':>10} {'Len Var':>12} {'First Token Variety':>20}")
    print("-" * 90)
    
    for temp, data in sorted(results.items()):
        div = data["diversity"]
        print(
            f"{temp:>6.1f} "
            f"{div['unique_ratio']*100:>9.1f}% "
            f"{div['avg_length']:>9.1f} "
            f"{div['length_variance']:>11.1f} "
            f"{div['first_token_variety']:>19}"
        )


def print_sample_outputs(results: Dict[float, Dict], max_samples: int = 2) -> None:
    """Print sample outputs for each temperature."""
    print("\n" + "="*90)
    print("SAMPLE OUTPUTS")
    print("="*90)
    
    for temp, data in sorted(results.items()):
        print(f"\nTemperature = {temp:.1f}:")
        print("-" * 90)
        
        for i, response in enumerate(data["responses"][:max_samples], 1):
            print(f"\n  Sample {i}:")
            print(f"  {response[:200]}{'...' if len(response) > 200 else ''}")


async def demo_temperature_range():
    """Demo: Compare temperature range from 0.0 to 2.0."""
    print("="*90)
    print("DEMO 1: Temperature Range Comparison")
    print("="*90)
    
    prompt = "Complete this sentence: The best thing about artificial intelligence is"
    temperatures = [0.0, 0.3, 0.7, 1.0, 1.5]
    
    print(f"\nPrompt: '{prompt}'")
    print(f"Generating {5} samples at each temperature...")
    
    results = await compare_temperatures(prompt, temperatures, samples_per_temp=5)
    
    print_comparison_table(results)
    print_sample_outputs(results, max_samples=2)


async def demo_task_specific():
    """Demo: Optimal temperature for different tasks."""
    print("\n" + "="*90)
    print("DEMO 2: Task-Specific Temperature Optimization")
    print("="*90)
    
    tasks = {
        "Classification": {
            "prompt": "Classify the sentiment of this text as positive, negative, or neutral: 'I love this product!'",
            "optimal_temp": 0.0,
        },
        "Creative Writing": {
            "prompt": "Write the first sentence of a mystery novel:",
            "optimal_temp": 1.0,
        },
        "Summarization": {
            "prompt": "Summarize in one sentence: Machine learning is a subset of AI.",
            "optimal_temp": 0.3,
        },
    }
    
    for task_name, task_data in tasks.items():
        print(f"\n{task_name}:")
        print(f"  Prompt: {task_data['prompt'][:80]}...")
        print(f"  Optimal temperature: {task_data['optimal_temp']}")
        
        # Test at optimal vs suboptimal temperature
        temps = [task_data['optimal_temp'], 1.5 if task_data['optimal_temp'] < 1.0 else 0.0]
        
        results = await compare_temperatures(
            task_data['prompt'], temps, samples_per_temp=3
        )
        
        for temp, data in sorted(results.items()):
            div = data['diversity']
            print(f"\n  Temperature {temp}:")
            print(f"    Unique responses: {div['unique_count']}/{div['total_count']}")
            print(f"    Sample: {data['responses'][0][:100]}...")


async def demo_determinism():
    """Demo: Determinism at temperature=0.0."""
    print("\n" + "="*90)
    print("DEMO 3: Determinism at Temperature=0.0")
    print("="*90)
    
    prompt = "What is 2 + 2?"
    
    print(f"\nPrompt: '{prompt}'")
    print("Generating 5 responses at temperature=0.0...")
    
    responses = await generate_at_temperature(prompt, temperature=0.0, num_samples=5)
    
    print("\nResponses:")
    for i, response in enumerate(responses, 1):
        print(f"  {i}. {response}")
    
    # Check if all responses are identical
    if len(set(responses)) == 1:
        print("\n✅ All responses are identical (deterministic)")
    else:
        print(f"\n⚠️ Got {len(set(responses))} unique responses (not perfectly deterministic)")
        print("   (Some variation is possible due to model updates or provider differences)")


async def demo_creativity_spectrum():
    """Demo: Creativity spectrum from low to high temperature."""
    print("\n" + "="*90)
    print("DEMO 4: Creativity Spectrum")
    print("="*90)
    
    prompt = "Describe a sunset in one sentence:"
    temperatures = [0.0, 0.5, 1.0, 1.5, 2.0]
    
    print(f"\nPrompt: '{prompt}'")
    
    for temp in temperatures:
        print(f"\nTemperature = {temp:.1f}:")
        
        responses = await generate_at_temperature(prompt, temp, num_samples=2)
        
        for i, response in enumerate(responses, 1):
            print(f"  {i}. {response}")


async def demo_real_world_example():
    """Demo: Real-world example with customer support."""
    print("\n" + "="*90)
    print("DEMO 5: Real-World Example - Customer Support")
    print("="*90)
    
    customer_query = "My order hasn't arrived yet. It's been 2 weeks!"
    
    print(f"\nCustomer query: '{customer_query}'")
    
    scenarios = {
        "Too robotic (temp=0.0)": 0.0,
        "Balanced (temp=0.7)": 0.7,
        "Too creative (temp=1.5)": 1.5,
    }
    
    for scenario, temp in scenarios.items():
        print(f"\n{scenario}:")
        
        response = await generate_at_temperature(
            f"You are a customer support agent. Respond to: '{customer_query}'",
            temperature=temp,
            num_samples=1,
        )
        
        print(f"  {response[0]}")


async def main():
    """Run all temperature demos."""
    print("="*90)
    print("🌡️  TEMPERATURE EXPLORATION DEMO")
    print("="*90)
    
    settings = get_settings()
    
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        print("\n⚠️  Warning: No API keys found in environment.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run live demos.")
        print("   Continuing with mock demonstrations...\n")
        return
    
    # Run all demos
    await demo_temperature_range()
    await demo_task_specific()
    await demo_determinism()
    await demo_creativity_spectrum()
    await demo_real_world_example()
    
    print("\n" + "="*90)
    print("✅ Demo complete!")
    print("="*90)
    print("\nKey takeaways:")
    print("  • Temperature=0.0: Deterministic, same output every time")
    print("  • Temperature=0.3-0.7: Balanced, slight variety")
    print("  • Temperature=1.0+: Creative, high diversity")
    print("  • Match temperature to task type")
    print("  • Lower temperature for factual/deterministic tasks")
    print("  • Higher temperature for creative/diverse tasks")


if __name__ == "__main__":
    asyncio.run(main())
