"""
Zero-shot prompting: single instruction, no examples.

Use when:
- Task is simple and well-defined
- LLM likely has training data for task
- Token budget is tight

Cost: ~50-200 tokens per query
Quality: ⭐⭐⭐ (good for simple tasks)

Examples:
- Sentiment classification
- Text summarization
- Translation
- Simple Q&A
"""

import asyncio
import logging
from typing import Any

from core.llm import chat
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


async def run(
    query: str,
    instruction: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
) -> LLMResponse:
    """
    Run zero-shot prompting.

    Args:
        query: User query or input text
        instruction: Optional task instruction (default: generic assistant)
        model: Model to use (default: from config)
        temperature: Sampling temperature (default: 0.0 for consistency)

    Returns:
        LLMResponse with result, tokens, and cost

    Example:
        >>> result = await zero_shot.run(
        ...     "I absolutely loved this movie!",
        ...     instruction="Classify the sentiment as Positive, Negative, or Neutral."
        ... )
        >>> print(result.text)
        Positive
        >>> print(f"Cost: ${result.usd_cost:.4f}")
        Cost: $0.0001
    """
    # Build prompt
    if instruction:
        prompt = f"{instruction}\n\nInput: {query}\n\nOutput:"
    else:
        prompt = query

    messages = [{"role": "user", "content": prompt}]

    # Call LLM
    response = await chat(
        messages,
        model=model,
        temperature=temperature,
        cache=True,  # Cache for repeated queries
    )

    logger.info(
        f"Zero-shot complete: {response.total_tokens} tokens, ${response.usd_cost:.4f}"
    )

    return response


async def sentiment_analysis(text: str) -> str:
    """
    Classify sentiment (zero-shot).

    Args:
        text: Text to analyze

    Returns:
        Sentiment label: "Positive", "Negative", or "Neutral"

    Cost: ~$0.0001 per classification (Haiku)

    Example:
        >>> sentiment = await zero_shot.sentiment_analysis("I love this!")
        >>> print(sentiment)
        Positive
    """
    instruction = (
        "Classify the sentiment of the following text as exactly one of: "
        "Positive, Negative, or Neutral. "
        "Respond with only the label, nothing else."
    )

    result = await run(text, instruction=instruction)
    return result.text.strip()


async def summarize(text: str, max_words: int = 50) -> str:
    """
    Summarize text (zero-shot).

    Args:
        text: Text to summarize
        max_words: Maximum words in summary

    Returns:
        Summary text

    Cost: ~$0.0002 per summarization (Haiku)

    Example:
        >>> summary = await zero_shot.summarize("Long article text...", max_words=30)
        >>> print(summary)
        The article discusses...
    """
    instruction = (
        f"Summarize the following text in {max_words} words or less. "
        "Be concise and capture key points."
    )

    result = await run(text, instruction=instruction)
    return result.text.strip()


async def extract_entities(text: str) -> list[dict[str, str]]:
    """
    Extract named entities (zero-shot).

    Args:
        text: Text to extract from

    Returns:
        List of entities with type and text

    Cost: ~$0.0002 per extraction (Haiku)

    Example:
        >>> entities = await zero_shot.extract_entities(
        ...     "Apple Inc. was founded by Steve Jobs in Cupertino."
        ... )
        >>> print(entities)
        [
            {"type": "ORG", "text": "Apple Inc."},
            {"type": "PERSON", "text": "Steve Jobs"},
            {"type": "LOC", "text": "Cupertino"}
        ]
    """
    instruction = """Extract named entities from the text.

Return JSON array of entities:
[
  {"type": "PERSON", "text": "entity text"},
  {"type": "ORG", "text": "entity text"},
  {"type": "LOC", "text": "entity text"}
]

Entity types: PERSON, ORG (organization), LOC (location), DATE, MONEY"""

    result = await run(text, instruction=instruction)

    # Parse JSON response
    import json

    try:
        entities = json.loads(result.text.strip())
        return entities
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse entities: {result.text}")
        return []


async def translate(text: str, target_language: str = "Spanish") -> str:
    """
    Translate text (zero-shot).

    Args:
        text: Text to translate
        target_language: Target language (default: Spanish)

    Returns:
        Translated text

    Cost: ~$0.0001 per translation (Haiku)

    Example:
        >>> translated = await zero_shot.translate("Hello world", "French")
        >>> print(translated)
        Bonjour le monde
    """
    instruction = f"Translate the following text to {target_language}. Return only the translation."

    result = await run(text, instruction=instruction)
    return result.text.strip()


# Benchmark function
async def benchmark(num_queries: int = 100) -> dict[str, Any]:
    """
    Benchmark zero-shot prompting.

    Args:
        num_queries: Number of test queries

    Returns:
        Benchmark results with cost and latency metrics

    Example:
        >>> results = await zero_shot.benchmark(100)
        >>> print(f"Avg cost: ${results['avg_cost']:.4f}")
        >>> print(f"P95 latency: {results['p95_latency_ms']:.0f}ms")
    """
    import time

    test_queries = [
        "I love this product!",
        "This is terrible.",
        "It's okay, nothing special.",
    ] * (num_queries // 3 + 1)

    costs = []
    latencies = []

    for query in test_queries[:num_queries]:
        start = time.time()
        result = await sentiment_analysis(query)
        latency_ms = (time.time() - start) * 1000

        costs.append(result.usd_cost if hasattr(result, "usd_cost") else 0.0001)
        latencies.append(latency_ms)

    latencies.sort()

    return {
        "num_queries": num_queries,
        "total_cost": sum(costs),
        "avg_cost": sum(costs) / len(costs),
        "avg_latency_ms": sum(latencies) / len(latencies),
        "p95_latency_ms": latencies[int(len(latencies) * 0.95)],
        "p99_latency_ms": latencies[int(len(latencies) * 0.99)],
    }


# Demo script
async def main():
    """Demo zero-shot prompting."""
    print("=" * 60)
    print("Zero-Shot Prompting Demo")
    print("=" * 60)

    # 1. Sentiment analysis
    print("\n1. Sentiment Analysis")
    print("-" * 60)
    texts = [
        "I absolutely love this product! Best purchase ever!",
        "Terrible quality. Very disappointed.",
        "It's okay. Does what it says.",
    ]

    for text in texts:
        result = await run(
            text,
            instruction="Classify sentiment as Positive, Negative, or Neutral.",
        )
        print(f"Text: {text}")
        print(f"Sentiment: {result.text}")
        print(f"Tokens: {result.total_tokens}, Cost: ${result.usd_cost:.4f}\n")

    # 2. Summarization
    print("\n2. Text Summarization")
    print("-" * 60)
    long_text = """
    Artificial intelligence (AI) is transforming industries worldwide.
    From healthcare to finance, AI systems are enabling unprecedented
    automation and insights. However, concerns about bias, privacy,
    and job displacement remain significant challenges that must be
    addressed as the technology continues to evolve.
    """

    result = await summarize(long_text, max_words=20)
    print(f"Original: {long_text.strip()}")
    print(f"Summary: {result}")
    print()

    # 3. Translation
    print("\n3. Translation")
    print("-" * 60)
    original = "Hello, how are you today?"
    translated = await translate(original, "French")
    print(f"English: {original}")
    print(f"French: {translated}")

    # 4. Cost summary
    print("\n" + "=" * 60)
    print("Cost Summary")
    print("=" * 60)
    print("Zero-shot is the most cost-efficient pattern:")
    print("- Sentiment: ~$0.0001 per query")
    print("- Summary: ~$0.0002 per query")
    print("- Translation: ~$0.0001 per query")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
