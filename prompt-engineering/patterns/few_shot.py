"""
Few-shot prompting: provide 2-5 examples before the query.

Use when:
- Task requires specific formatting
- Pattern learning from examples
- Zero-shot quality insufficient

Cost: ~200-800 tokens per query (examples + query)
Quality: ⭐⭐⭐⭐ (better than zero-shot)

Examples:
- Custom entity extraction
- Structured output formatting
- Style transfer
- Complex classification
"""

import asyncio
import logging
from typing import Any

from core.llm import chat
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


def build_few_shot_prompt(
    examples: list[dict[str, str]],
    query: str,
    instruction: str | None = None,
) -> str:
    """
    Build few-shot prompt from examples.

    Args:
        examples: List of {"input": "...", "output": "..."} dicts
        query: User query
        instruction: Optional task instruction

    Returns:
        Formatted few-shot prompt

    Example:
        >>> examples = [
        ...     {"input": "I love it!", "output": "Positive"},
        ...     {"input": "Terrible.", "output": "Negative"},
        ... ]
        >>> prompt = build_few_shot_prompt(examples, "It's great!", "Classify sentiment")
    """
    parts = []

    if instruction:
        parts.append(instruction)
        parts.append("")

    # Add examples
    for i, example in enumerate(examples, 1):
        parts.append(f"Example {i}:")
        parts.append(f"Input: {example['input']}")
        parts.append(f"Output: {example['output']}")
        parts.append("")

    # Add query
    parts.append("Now, apply the same pattern:")
    parts.append(f"Input: {query}")
    parts.append("Output:")

    return "\n".join(parts)


async def run(
    query: str,
    examples: list[dict[str, str]],
    instruction: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
) -> LLMResponse:
    """
    Run few-shot prompting.

    Args:
        query: User query
        examples: 2-5 example input/output pairs
        instruction: Optional task instruction
        model: Model to use
        temperature: Sampling temperature

    Returns:
        LLMResponse with result

    Example:
        >>> examples = [
        ...     {"input": "Apple Inc. → Tech", "output": "Technology"},
        ...     {"input": "Goldman Sachs → Finance", "output": "Financial Services"},
        ... ]
        >>> result = await few_shot.run("Tesla → Auto", examples=examples)
        >>> print(result.text)
        Automotive
    """
    # Build prompt
    prompt = build_few_shot_prompt(examples, query, instruction)

    messages = [{"role": "user", "content": prompt}]

    # Call LLM
    response = await chat(
        messages,
        model=model,
        temperature=temperature,
        cache=True,
    )

    logger.info(
        f"Few-shot complete: {response.total_tokens} tokens, ${response.usd_cost:.4f}"
    )

    return response


async def sentiment_analysis(text: str) -> str:
    """
    Classify sentiment with few-shot examples.

    Args:
        text: Text to classify

    Returns:
        Sentiment label

    Cost: ~$0.0003 per classification (Haiku)

    Example:
        >>> sentiment = await few_shot.sentiment_analysis("This is amazing!")
        >>> print(sentiment)
        Positive
    """
    examples = [
        {"input": "I love this product! It's amazing!", "output": "Positive"},
        {"input": "Terrible quality. Very disappointed.", "output": "Negative"},
        {"input": "It's okay. Nothing special.", "output": "Neutral"},
        {"input": "Highly recommend! Best purchase ever!", "output": "Positive"},
        {"input": "Waste of money. Do not buy.", "output": "Negative"},
    ]

    instruction = "Classify sentiment as Positive, Negative, or Neutral."

    result = await run(text, examples=examples[:3], instruction=instruction)
    return result.text.strip()


async def entity_extraction_structured(text: str) -> dict[str, list[str]]:
    """
    Extract entities with structured output (few-shot).

    Args:
        text: Text to extract from

    Returns:
        Dict with entity types as keys

    Cost: ~$0.0004 per extraction (Haiku)

    Example:
        >>> entities = await few_shot.entity_extraction_structured(
        ...     "Apple Inc. CEO Tim Cook visited Paris last week."
        ... )
        >>> print(entities)
        {
            "organizations": ["Apple Inc."],
            "people": ["Tim Cook"],
            "locations": ["Paris"]
        }
    """
    examples = [
        {
            "input": "Microsoft CEO Satya Nadella spoke in Seattle.",
            "output": '{"organizations": ["Microsoft"], "people": ["Satya Nadella"], "locations": ["Seattle"]}',
        },
        {
            "input": "Google announced a new AI model yesterday.",
            "output": '{"organizations": ["Google"], "people": [], "locations": []}',
        },
        {
            "input": "Elon Musk founded Tesla and SpaceX in California.",
            "output": '{"organizations": ["Tesla", "SpaceX"], "people": ["Elon Musk"], "locations": ["California"]}',
        },
    ]

    instruction = "Extract named entities and return as JSON."

    result = await run(text, examples=examples, instruction=instruction)

    # Parse JSON
    import json

    try:
        entities = json.loads(result.text.strip())
        return entities
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse entities: {result.text}")
        return {"organizations": [], "people": [], "locations": []}


async def style_transfer(text: str, target_style: str = "formal") -> str:
    """
    Transfer text to different style (few-shot).

    Args:
        text: Text to transform
        target_style: Target style (formal, casual, professional)

    Returns:
        Transformed text

    Cost: ~$0.0003 per transformation (Haiku)

    Example:
        >>> formal = await few_shot.style_transfer(
        ...     "Hey! What's up? Wanna grab lunch?",
        ...     target_style="formal"
        ... )
        >>> print(formal)
        Hello. How are you? Would you like to have lunch together?
    """
    if target_style == "formal":
        examples = [
            {
                "input": "Thanks a lot! Really appreciate it.",
                "output": "Thank you very much. I sincerely appreciate your assistance.",
            },
            {
                "input": "Nope, can't make it today.",
                "output": "Unfortunately, I am unable to attend today.",
            },
            {
                "input": "Let me know ASAP!",
                "output": "Please inform me at your earliest convenience.",
            },
        ]
    elif target_style == "casual":
        examples = [
            {
                "input": "I would appreciate your assistance with this matter.",
                "output": "Hey, could you help me out with this?",
            },
            {
                "input": "I am unable to attend the meeting.",
                "output": "Can't make it to the meeting, sorry!",
            },
            {
                "input": "Please inform me at your earliest convenience.",
                "output": "Let me know when you can!",
            },
        ]
    else:
        examples = [
            {
                "input": "Hey what's up?",
                "output": "Hello, how are you?",
            },
        ]

    instruction = f"Transform the text to {target_style} style."

    result = await run(text, examples=examples, instruction=instruction)
    return result.text.strip()


async def custom_classification(
    text: str,
    examples: list[dict[str, str]],
    categories: list[str],
) -> str:
    """
    Custom classification with user-provided examples.

    Args:
        text: Text to classify
        examples: Custom examples
        categories: List of category labels

    Returns:
        Predicted category

    Cost: ~$0.0003-0.0005 per classification (Haiku)

    Example:
        >>> examples = [
        ...     {"input": "Bug in login flow", "output": "bug"},
        ...     {"input": "Add dark mode", "output": "feature"},
        ...     {"input": "Improve performance", "output": "enhancement"},
        ... ]
        >>> category = await few_shot.custom_classification(
        ...     "Fix crash on startup",
        ...     examples=examples,
        ...     categories=["bug", "feature", "enhancement"]
        ... )
        >>> print(category)
        bug
    """
    categories_str = ", ".join(categories)
    instruction = f"Classify the text into one of: {categories_str}"

    result = await run(text, examples=examples, instruction=instruction)
    return result.text.strip()


# Benchmark function
async def benchmark(num_queries: int = 100) -> dict[str, Any]:
    """
    Benchmark few-shot prompting.

    Args:
        num_queries: Number of test queries

    Returns:
        Benchmark results with cost and latency metrics
    """
    import time

    test_queries = [
        "I love this product!",
        "This is terrible.",
        "It's okay, nothing special.",
    ] * (num_queries // 3 + 1)

    costs = []
    latencies = []
    tokens_list = []

    for query in test_queries[:num_queries]:
        start = time.time()

        examples = [
            {"input": "Great quality!", "output": "Positive"},
            {"input": "Very bad.", "output": "Negative"},
            {"input": "It's fine.", "output": "Neutral"},
        ]

        result = await run(query, examples=examples)
        latency_ms = (time.time() - start) * 1000

        costs.append(result.usd_cost)
        latencies.append(latency_ms)
        tokens_list.append(result.total_tokens)

    latencies.sort()

    return {
        "num_queries": num_queries,
        "total_cost": sum(costs),
        "avg_cost": sum(costs) / len(costs),
        "avg_tokens": sum(tokens_list) / len(tokens_list),
        "avg_latency_ms": sum(latencies) / len(latencies),
        "p95_latency_ms": latencies[int(len(latencies) * 0.95)],
        "p99_latency_ms": latencies[int(len(latencies) * 0.99)],
    }


# Demo script
async def main():
    """Demo few-shot prompting."""
    print("=" * 60)
    print("Few-Shot Prompting Demo")
    print("=" * 60)

    # 1. Sentiment with examples
    print("\n1. Sentiment Analysis (Few-Shot)")
    print("-" * 60)

    examples = [
        {"input": "Love it!", "output": "Positive"},
        {"input": "Hate it.", "output": "Negative"},
        {"input": "It's okay.", "output": "Neutral"},
    ]

    test_texts = [
        "This is fantastic!",
        "Not impressed at all.",
        "Meets expectations.",
    ]

    for text in test_texts:
        result = await run(text, examples=examples)
        print(f"Text: {text}")
        print(f"Sentiment: {result.text}")
        print(f"Tokens: {result.total_tokens}, Cost: ${result.usd_cost:.4f}\n")

    # 2. Structured entity extraction
    print("\n2. Structured Entity Extraction")
    print("-" * 60)

    text = "Apple CEO Tim Cook announced new products in Cupertino."
    entities = await entity_extraction_structured(text)
    print(f"Text: {text}")
    print(f"Entities: {entities}\n")

    # 3. Style transfer
    print("\n3. Style Transfer")
    print("-" * 60)

    casual = "Hey! What's up? Wanna grab lunch?"
    formal = await style_transfer(casual, target_style="formal")
    print(f"Casual: {casual}")
    print(f"Formal: {formal}\n")

    # 4. Cost comparison
    print("\n" + "=" * 60)
    print("Zero-Shot vs Few-Shot Comparison")
    print("=" * 60)
    print("Zero-shot: ~120 tokens, $0.0001")
    print("Few-shot: ~450 tokens, $0.0003")
    print("Improvement: ~7% better accuracy, 3x cost")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
