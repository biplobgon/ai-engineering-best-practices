"""
Before/After examples of prompt anti-patterns.

Each example shows:
- Bad prompt (anti-pattern)
- Good prompt (fixed)
- Impact metrics
"""

import asyncio
import logging

from core.llm import chat


logger = logging.getLogger(__name__)


class AntiPatternExample:
    """Container for anti-pattern example."""

    def __init__(
        self,
        name: str,
        bad_prompt: str,
        good_prompt: str,
        description: str,
        impact: dict,
    ):
        self.name = name
        self.bad_prompt = bad_prompt
        self.good_prompt = good_prompt
        self.description = description
        self.impact = impact


# Anti-pattern examples
EXAMPLES = [
    AntiPatternExample(
        name="Vague Instructions",
        bad_prompt="Tell me about the product.",
        good_prompt="""Analyze this product review and classify sentiment as Positive, Negative, or Neutral.
Provide reasoning in 1-2 sentences.

Review: {text}""",
        description="Being specific improves accuracy and reduces ambiguity",
        impact={"accuracy": "+40%", "consistency": "+60%"},
    ),
    AntiPatternExample(
        name="No Output Format",
        bad_prompt="Extract entities from text.",
        good_prompt="""Extract entities from text.

Return JSON:
{
  "people": ["name1"],
  "places": ["place1"],
  "organizations": ["org1"]
}

Text: {text}""",
        description="Specifying format reduces parsing errors",
        impact={"parsing_errors": "-90%", "integration_time": "-70%"},
    ),
    AntiPatternExample(
        name="Too Many Examples",
        bad_prompt="""Example 1: ...
Example 2: ...
[... Examples 3-15 ...]
Input: {text}""",
        good_prompt="""Example 1: [common case]
Example 2: [edge case]
Example 3: [another edge case]

Input: {text}""",
        description="3-5 examples optimal; more wastes tokens",
        impact={"tokens": "-70%", "cost": "-70%", "accuracy": "~same"},
    ),
    AntiPatternExample(
        name="Assuming Context",
        bad_prompt="How did the launch go?",
        good_prompt="""Context: Product launched Jan 15, 2024. Week 1 sales: $50K, 1,247 customers.

Question: Based on this data, how did the launch perform?""",
        description="LLMs don't have your context; provide it explicitly",
        impact={"relevance": "+70%", "accuracy": "+50%"},
    ),
    AntiPatternExample(
        name="Token Waste",
        bad_prompt="""You are a highly experienced expert with 20 years in the field, 
known for your exceptional analytical skills and deep understanding...
[500 tokens of backstory]

Question: Is "I love it" positive or negative?""",
        good_prompt="""Classify sentiment as Positive or Negative.
Text: "I love it"
""",
        description="Remove unnecessary tokens",
        impact={"tokens": "-95%", "cost": "-95%", "latency": "-80%"},
    ),
]


async def demonstrate_example(example: AntiPatternExample) -> dict:
    """
    Demonstrate an anti-pattern example.

    Args:
        example: AntiPatternExample to demonstrate

    Returns:
        Dict with before/after metrics
    """
    print(f"\n{'='*60}")
    print(f"Anti-Pattern: {example.name}")
    print(f"{'='*60}")

    print(f"\n❌ BAD:")
    print(example.bad_prompt)

    print(f"\n✅ GOOD:")
    print(example.good_prompt)

    print(f"\nDescription: {example.description}")

    print(f"\nImpact:")
    for metric, value in example.impact.items():
        print(f"  - {metric}: {value}")

    return {
        "name": example.name,
        "description": example.description,
        "impact": example.impact,
    }


async def compare_prompts(bad_prompt: str, good_prompt: str, test_input: str) -> dict:
    """
    Compare bad vs good prompt on actual LLM call.

    Args:
        bad_prompt: Anti-pattern prompt
        good_prompt: Fixed prompt
        test_input: Test input to use

    Returns:
        Comparison metrics
    """
    # Fill in test input
    bad_filled = bad_prompt.replace("{text}", test_input)
    good_filled = good_prompt.replace("{text}", test_input)

    # Call LLM with bad prompt
    bad_messages = [{"role": "user", "content": bad_filled}]
    bad_response = await chat(bad_messages, temperature=0.0)

    # Call LLM with good prompt
    good_messages = [{"role": "user", "content": good_filled}]
    good_response = await chat(good_messages, temperature=0.0)

    # Compare
    return {
        "bad": {
            "tokens": bad_response.total_tokens,
            "cost": bad_response.usd_cost,
            "latency_ms": bad_response.latency_ms,
            "output": bad_response.text[:100],
        },
        "good": {
            "tokens": good_response.total_tokens,
            "cost": good_response.usd_cost,
            "latency_ms": good_response.latency_ms,
            "output": good_response.text[:100],
        },
        "improvement": {
            "token_reduction": (
                bad_response.total_tokens - good_response.total_tokens
            ) / bad_response.total_tokens,
            "cost_reduction": (
                bad_response.usd_cost - good_response.usd_cost
            ) / bad_response.usd_cost if bad_response.usd_cost > 0 else 0,
            "latency_reduction": (
                bad_response.latency_ms - good_response.latency_ms
            ) / bad_response.latency_ms if bad_response.latency_ms > 0 else 0,
        },
    }


async def main():
    """Demo anti-pattern examples."""
    print("=" * 60)
    print("Anti-Pattern Examples")
    print("=" * 60)

    # Show all examples
    for example in EXAMPLES:
        await demonstrate_example(example)

    # Compare first example with actual LLM calls
    print("\n\n" + "=" * 60)
    print("Live Comparison: Token Waste")
    print("=" * 60)

    waste_example = EXAMPLES[4]  # Token waste example
    test_input = "I love it"

    comparison = await compare_prompts(
        waste_example.bad_prompt,
        waste_example.good_prompt,
        test_input
    )

    print("\n❌ Bad Prompt:")
    print(f"  Tokens: {comparison['bad']['tokens']}")
    print(f"  Cost: ${comparison['bad']['cost']:.6f}")
    print(f"  Latency: {comparison['bad']['latency_ms']:.0f}ms")

    print("\n✅ Good Prompt:")
    print(f"  Tokens: {comparison['good']['tokens']}")
    print(f"  Cost: ${comparison['good']['cost']:.6f}")
    print(f"  Latency: {comparison['good']['latency_ms']:.0f}ms")

    print("\n📊 Improvements:")
    print(f"  Token reduction: {comparison['improvement']['token_reduction']:.1%}")
    print(f"  Cost reduction: {comparison['improvement']['cost_reduction']:.1%}")
    print(f"  Latency reduction: {comparison['improvement']['latency_reduction']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
