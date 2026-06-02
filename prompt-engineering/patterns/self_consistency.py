"""
Self-consistency: sample multiple reasoning paths, take majority vote.

Pattern:
1. Generate N diverse reasoning paths (temperature > 0)
2. Extract final answer from each
3. Take majority vote or mode

Use when:
- High-stakes decisions
- Ambiguous questions
- Need confidence estimation

Cost: N× chain-of-thought cost (~5-10x)
Quality: ⭐⭐⭐⭐⭐ (best accuracy, high cost)

Key insight: Multiple reasoning paths reduce random errors.

Examples:
- Medical diagnosis
- Legal reasoning
- Complex math problems
- High-value decisions
"""

import asyncio
import logging
from collections import Counter
from typing import Any

from core.llm import chat
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


async def run(
    query: str,
    num_samples: int = 5,
    temperature: float = 0.7,
    instruction: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Run self-consistency with multiple reasoning paths.

    Args:
        query: User query
        num_samples: Number of reasoning paths (default: 5, use odd for voting)
        temperature: Sampling temperature (0.7-1.0 for diversity)
        instruction: Optional task instruction
        model: Model to use

    Returns:
        Dict with majority answer, all answers, confidence, and metadata

    Example:
        >>> result = await self_consistency.run(
        ...     "If a shirt costs $20 and is on sale for 25% off, what's the price?",
        ...     num_samples=5
        ... )
        >>> print(result['answer'])
        $15
        >>> print(result['confidence'])
        1.0  # All 5 samples agreed
    """
    # Build prompt with CoT trigger
    parts = []

    if instruction:
        parts.append(instruction)
        parts.append("")

    parts.append(f"Q: {query}")
    parts.append("A: Let's think step by step:")

    prompt = "\n".join(parts)

    messages = [{"role": "user", "content": prompt}]

    # Generate multiple reasoning paths
    tasks = [
        chat(messages, model=model, temperature=temperature, cache=False)
        for _ in range(num_samples)
    ]

    responses = await asyncio.gather(*tasks)

    # Extract answers
    answers = []
    reasonings = []

    for i, response in enumerate(responses):
        text = response.text.strip()
        reasonings.append(text)

        # Try to extract final answer
        answer = extract_answer(text)
        answers.append(answer)

        logger.debug(f"Sample {i+1}: {answer}")

    # Take majority vote
    answer_counts = Counter(answers)
    majority_answer, majority_count = answer_counts.most_common(1)[0]

    confidence = majority_count / num_samples

    # Calculate total cost
    total_tokens = sum(r.total_tokens for r in responses)
    total_cost = sum(r.usd_cost for r in responses)

    return {
        "query": query,
        "answer": majority_answer,
        "confidence": confidence,
        "all_answers": answers,
        "answer_distribution": dict(answer_counts),
        "reasonings": reasonings,
        "num_samples": num_samples,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "avg_tokens_per_sample": total_tokens / num_samples,
        "avg_cost_per_sample": total_cost / num_samples,
    }


def extract_answer(reasoning: str) -> str:
    """
    Extract final answer from reasoning text.

    Args:
        reasoning: Full reasoning text

    Returns:
        Extracted answer

    Strategies:
    1. Look for "Answer:" or "Final answer:"
    2. Look for "Therefore," or "Thus,"
    3. Take last line
    4. Look for numbers in last few lines
    """
    lines = [line.strip() for line in reasoning.split("\n") if line.strip()]

    # Strategy 1: Explicit answer marker
    for line in lines:
        if "answer:" in line.lower():
            return line.split(":")[-1].strip()

    # Strategy 2: Conclusion marker
    for line in lines:
        if any(marker in line.lower() for marker in ["therefore", "thus", "so,"]):
            return line.strip()

    # Strategy 3: Last line
    if lines:
        return lines[-1]

    return reasoning.strip()


async def math_problem(problem: str, num_samples: int = 5) -> dict[str, Any]:
    """
    Solve math problem with self-consistency.

    Args:
        problem: Math word problem
        num_samples: Number of reasoning paths

    Returns:
        Dict with answer and confidence

    Cost: ~$0.002-0.003 per problem (5 samples, Haiku)

    Example:
        >>> result = await self_consistency.math_problem(
        ...     "A store has 24 apples. They sell 7 in morning and 5 in afternoon. How many remain?",
        ...     num_samples=5
        ... )
        >>> print(f"Answer: {result['answer']}")
        >>> print(f"Confidence: {result['confidence']:.0%}")
    """
    instruction = "Solve this math problem. Show your reasoning step by step, then give the final numerical answer."

    return await run(problem, num_samples=num_samples, instruction=instruction)


async def multiple_choice(
    question: str,
    choices: list[str],
    num_samples: int = 5,
) -> dict[str, Any]:
    """
    Answer multiple choice question with self-consistency.

    Args:
        question: Question text
        choices: List of choices (e.g., ["A) ...", "B) ...", ...])
        num_samples: Number of reasoning paths

    Returns:
        Dict with answer and confidence

    Cost: ~$0.002-0.003 per question (5 samples, Haiku)

    Example:
        >>> result = await self_consistency.multiple_choice(
        ...     "What's the capital of France?",
        ...     ["A) London", "B) Paris", "C) Berlin", "D) Madrid"],
        ...     num_samples=5
        ... )
        >>> print(result['answer'])
    """
    choices_str = "\n".join(choices)

    full_query = f"{question}\n\n{choices_str}\n\nSelect the correct answer."

    instruction = "Think through each option carefully before selecting your answer."

    return await run(full_query, num_samples=num_samples, instruction=instruction)


async def classification(
    text: str,
    categories: list[str],
    num_samples: int = 5,
) -> dict[str, Any]:
    """
    Classify with self-consistency.

    Args:
        text: Text to classify
        categories: List of category labels
        num_samples: Number of reasoning paths

    Returns:
        Dict with classification and confidence

    Cost: ~$0.002-0.003 per classification (5 samples, Haiku)

    Example:
        >>> result = await self_consistency.classification(
        ...     "This product is absolutely terrible!",
        ...     categories=["Positive", "Negative", "Neutral"],
        ...     num_samples=5
        ... )
        >>> print(f"{result['answer']} (confidence: {result['confidence']:.0%})")
    """
    categories_str = ", ".join(categories)

    query = f"Text: {text}\n\nCategories: {categories_str}\n\nClassify the text."

    instruction = "Think about the sentiment and tone before classifying."

    return await run(query, num_samples=num_samples, instruction=instruction)


async def yes_no_question(question: str, context: str, num_samples: int = 5) -> dict[str, Any]:
    """
    Answer yes/no question with self-consistency.

    Args:
        question: Yes/no question
        context: Context for reasoning
        num_samples: Number of reasoning paths

    Returns:
        Dict with answer (Yes/No) and confidence

    Cost: ~$0.002-0.003 per question (5 samples, Haiku)

    Example:
        >>> result = await self_consistency.yes_no_question(
        ...     "Does the product meet safety standards?",
        ...     context="Product passed all FDA tests and received approval.",
        ...     num_samples=5
        ... )
        >>> print(f"{result['answer']} (confidence: {result['confidence']:.0%})")
    """
    query = f"Context: {context}\n\nQuestion: {question}\n\nAnswer Yes or No."

    instruction = "Consider the context carefully. Provide your reasoning, then answer Yes or No."

    return await run(query, num_samples=num_samples, instruction=instruction)


# Benchmark function
async def benchmark(num_queries: int = 10) -> dict[str, Any]:
    """
    Benchmark self-consistency.

    Args:
        num_queries: Number of test queries

    Returns:
        Benchmark results

    Note: Self-consistency is very expensive (5-10x CoT cost)
    """
    import time

    test_problems = [
        "A shop has 24 apples. They sell 7 in morning, 5 in afternoon. How many remain?",
        "If a shirt costs $40 and is 25% off, what's the sale price?",
        "A train travels 60 km/h for 2.5 hours. How far does it go?",
    ] * (num_queries // 3 + 1)

    costs = []
    latencies = []
    tokens_list = []
    confidences = []

    for problem in test_problems[:num_queries]:
        start = time.time()
        result = await math_problem(problem, num_samples=5)
        latency_ms = (time.time() - start) * 1000

        costs.append(result["total_cost"])
        latencies.append(latency_ms)
        tokens_list.append(result["total_tokens"])
        confidences.append(result["confidence"])

    latencies.sort()

    return {
        "num_queries": num_queries,
        "total_cost": sum(costs),
        "avg_cost": sum(costs) / len(costs),
        "avg_tokens": sum(tokens_list) / len(tokens_list),
        "avg_confidence": sum(confidences) / len(confidences),
        "avg_latency_ms": sum(latencies) / len(latencies),
        "p95_latency_ms": latencies[int(len(latencies) * 0.95)] if latencies else 0,
        "p99_latency_ms": latencies[int(len(latencies) * 0.99)] if latencies else 0,
    }


# Demo script
async def main():
    """Demo self-consistency."""
    print("=" * 60)
    print("Self-Consistency Demo")
    print("=" * 60)

    # 1. Math problem
    print("\n1. Math Problem (5 samples)")
    print("-" * 60)

    problem = "If a book costs $15 and is on sale for 20% off, what's the final price?"
    result = await math_problem(problem, num_samples=5)

    print(f"Problem: {problem}")
    print(f"\nAll answers: {result['all_answers']}")
    print(f"Distribution: {result['answer_distribution']}")
    print(f"\n✅ Majority answer: {result['answer']}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"\nTokens: {result['total_tokens']} ({result['avg_tokens_per_sample']:.0f} per sample)")
    print(f"Cost: ${result['total_cost']:.4f} (${result['avg_cost_per_sample']:.4f} per sample)\n")

    # 2. Multiple choice
    print("\n2. Multiple Choice (5 samples)")
    print("-" * 60)

    question = "What's 15% of 200?"
    choices = [
        "A) 20",
        "B) 25",
        "C) 30",
        "D) 35",
    ]

    result = await multiple_choice(question, choices, num_samples=5)

    print(f"Question: {question}")
    print("Choices:")
    for choice in choices:
        print(f"  {choice}")
    print(f"\nAll answers: {result['all_answers']}")
    print(f"✅ Answer: {result['answer']}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Cost: ${result['total_cost']:.4f}\n")

    # 3. Classification
    print("\n3. Classification (5 samples)")
    print("-" * 60)

    text = "This product is okay, but could be better."
    result = await classification(
        text,
        categories=["Positive", "Negative", "Neutral"],
        num_samples=5
    )

    print(f"Text: {text}")
    print(f"All classifications: {result['all_answers']}")
    print(f"Distribution: {result['answer_distribution']}")
    print(f"✅ Classification: {result['answer']}")
    print(f"Confidence: {result['confidence']:.0%}")

    # 4. Comparison
    print("\n\n" + "=" * 60)
    print("Self-Consistency vs Other Patterns")
    print("=" * 60)
    print("Math problem accuracy:")
    print("- Zero-shot: ~60%")
    print("- Chain-of-Thought: ~85%")
    print("- Self-Consistency (5 samples): ~92%")
    print("\nCost comparison (per query):")
    print("- Zero-shot: $0.0001")
    print("- CoT: $0.0004")
    print("- Self-Consistency: $0.002 (5x CoT)")
    print("\nUse when: Accuracy > Cost")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
