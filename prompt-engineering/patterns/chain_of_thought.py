"""
Chain-of-Thought (CoT) prompting: step-by-step reasoning.

Use when:
- Task requires multi-step reasoning
- Math, logic, or complex problem-solving
- Need to verify reasoning path

Cost: ~300-1000 tokens per query (includes reasoning steps)
Quality: ⭐⭐⭐⭐ (significantly better on reasoning tasks)

Key insight: Adding "Let's think step by step" triggers reasoning behavior.

Examples:
- Math word problems
- Logic puzzles
- Multi-step planning
- Causal reasoning
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
    few_shot_examples: list[dict[str, str]] | None = None,
) -> LLMResponse:
    """
    Run chain-of-thought prompting.

    Args:
        query: User query
        instruction: Optional task instruction
        model: Model to use
        temperature: Sampling temperature (0.0 for deterministic)
        few_shot_examples: Optional CoT examples (input + reasoning + output)

    Returns:
        LLMResponse with reasoning steps + answer

    Example:
        >>> result = await chain_of_thought.run(
        ...     "Roger has 5 tennis balls. He buys 2 more cans of tennis balls. "
        ...     "Each can has 3 balls. How many balls does he have now?"
        ... )
        >>> print(result.text)
        Let's think step by step:
        1. Roger starts with 5 balls
        2. He buys 2 cans, each with 3 balls: 2 × 3 = 6 balls
        3. Total: 5 + 6 = 11 balls
        Answer: 11 balls
    """
    # Build prompt
    parts = []

    if instruction:
        parts.append(instruction)
        parts.append("")

    # Add few-shot CoT examples if provided
    if few_shot_examples:
        for i, example in enumerate(few_shot_examples, 1):
            parts.append(f"Example {i}:")
            parts.append(f"Q: {example['input']}")
            parts.append(f"A: {example['reasoning']}")
            parts.append("")

    # Add query with CoT trigger
    parts.append("Q: " + query)
    parts.append("A: Let's think step by step:")

    prompt = "\n".join(parts)

    messages = [{"role": "user", "content": prompt}]

    # Call LLM
    response = await chat(
        messages,
        model=model,
        temperature=temperature,
        cache=False,  # Don't cache reasoning tasks
    )

    logger.info(
        f"CoT complete: {response.total_tokens} tokens, ${response.usd_cost:.4f}"
    )

    return response


async def math_problem(problem: str) -> dict[str, str]:
    """
    Solve math word problem with CoT.

    Args:
        problem: Math word problem

    Returns:
        Dict with 'reasoning' and 'answer' keys

    Cost: ~$0.0004 per problem (Haiku)

    Example:
        >>> result = await chain_of_thought.math_problem(
        ...     "A bakery makes 12 dozen cookies. They sell 85 cookies. How many remain?"
        ... )
        >>> print(result['reasoning'])
        >>> print(result['answer'])
    """
    instruction = "Solve the math problem. Show your reasoning step by step, then give the final answer."

    response = await run(problem, instruction=instruction)

    # Parse reasoning and answer
    text = response.text.strip()

    # Try to extract final answer
    lines = text.split("\n")
    reasoning = text
    answer = ""

    for line in reversed(lines):
        if "answer:" in line.lower() or "=" in line:
            answer = line.strip()
            break

    return {
        "reasoning": reasoning,
        "answer": answer,
        "tokens": response.total_tokens,
        "cost": response.usd_cost,
    }


async def logic_puzzle(puzzle: str) -> dict[str, str]:
    """
    Solve logic puzzle with CoT.

    Args:
        puzzle: Logic puzzle description

    Returns:
        Dict with reasoning and answer

    Cost: ~$0.0005 per puzzle (Haiku)

    Example:
        >>> puzzle = '''
        ... If all roses are flowers and some flowers fade quickly,
        ... can we conclude that some roses fade quickly?
        ... '''
        >>> result = await chain_of_thought.logic_puzzle(puzzle)
        >>> print(result['answer'])
    """
    instruction = "Solve this logic puzzle. Think through each step carefully."

    response = await run(puzzle, instruction=instruction)

    text = response.text.strip()

    return {
        "reasoning": text,
        "answer": text.split("\n")[-1] if "\n" in text else text,
        "tokens": response.total_tokens,
        "cost": response.usd_cost,
    }


async def multi_step_planning(goal: str, constraints: list[str] | None = None) -> dict[str, Any]:
    """
    Create multi-step plan with CoT.

    Args:
        goal: Goal to achieve
        constraints: Optional constraints

    Returns:
        Dict with plan steps

    Cost: ~$0.0005 per plan (Haiku)

    Example:
        >>> result = await chain_of_thought.multi_step_planning(
        ...     "Organize a tech conference for 500 people",
        ...     constraints=["Budget: $50k", "Timeline: 3 months"]
        ... )
        >>> for step in result['steps']:
        ...     print(f"- {step}")
    """
    prompt_parts = [f"Goal: {goal}"]

    if constraints:
        prompt_parts.append("\nConstraints:")
        for constraint in constraints:
            prompt_parts.append(f"- {constraint}")

    prompt_parts.append("\nCreate a step-by-step plan to achieve this goal.")

    prompt = "\n".join(prompt_parts)

    instruction = "Think through the requirements and create a detailed plan with steps."

    response = await run(prompt, instruction=instruction)

    # Parse steps
    text = response.text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    steps = []
    for line in lines:
        if line[0].isdigit() or line.startswith("-") or line.startswith("•"):
            # Remove numbering/bullets
            step = line.lstrip("0123456789.-•) ").strip()
            if step:
                steps.append(step)

    return {
        "goal": goal,
        "steps": steps,
        "reasoning": text,
        "tokens": response.total_tokens,
        "cost": response.usd_cost,
    }


async def causal_reasoning(scenario: str, question: str) -> dict[str, str]:
    """
    Answer causal reasoning question with CoT.

    Args:
        scenario: Background scenario
        question: Question about causality

    Returns:
        Dict with reasoning and answer

    Cost: ~$0.0004 per query (Haiku)

    Example:
        >>> result = await chain_of_thought.causal_reasoning(
        ...     scenario="Sales dropped 30% after price increase",
        ...     question="What likely caused the sales drop?"
        ... )
        >>> print(result['reasoning'])
    """
    prompt = f"Scenario: {scenario}\n\nQuestion: {question}"

    instruction = "Analyze the causal relationship. Consider multiple factors and think step by step."

    response = await run(prompt, instruction=instruction)

    return {
        "scenario": scenario,
        "question": question,
        "reasoning": response.text.strip(),
        "tokens": response.total_tokens,
        "cost": response.usd_cost,
    }


async def with_few_shot_examples(
    query: str,
    examples: list[dict[str, str]],
) -> LLMResponse:
    """
    CoT with few-shot examples (most powerful combination).

    Args:
        query: Query to solve
        examples: Examples with input + reasoning

    Returns:
        LLMResponse with reasoning

    Cost: ~$0.0006-0.001 per query (Haiku)

    Example:
        >>> examples = [{
        ...     "input": "5 + 3 × 2 = ?",
        ...     "reasoning": "Let's think step by step:\\n1. Order of operations: multiplication first\\n2. 3 × 2 = 6\\n3. 5 + 6 = 11\\nAnswer: 11"
        ... }]
        >>> result = await chain_of_thought.with_few_shot_examples(
        ...     "10 - 2 × 3 = ?",
        ...     examples=examples
        ... )
    """
    return await run(query, few_shot_examples=examples)


# Benchmark function
async def benchmark(num_queries: int = 50) -> dict[str, Any]:
    """
    Benchmark chain-of-thought prompting.

    Args:
        num_queries: Number of test queries

    Returns:
        Benchmark results

    Note: CoT is slower and more expensive than zero-shot/few-shot
    """
    import time

    test_problems = [
        "A shop has 24 apples. They sell 7 in the morning and 5 in the afternoon. How many remain?",
        "If a train travels 60 km/h for 2.5 hours, how far does it go?",
        "Sarah has $20. She spends $7.50 on lunch and $3.25 on coffee. How much is left?",
    ] * (num_queries // 3 + 1)

    costs = []
    latencies = []
    tokens_list = []

    for problem in test_problems[:num_queries]:
        start = time.time()
        result = await math_problem(problem)
        latency_ms = (time.time() - start) * 1000

        costs.append(result["cost"])
        latencies.append(latency_ms)
        tokens_list.append(result["tokens"])

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
    """Demo chain-of-thought prompting."""
    print("=" * 60)
    print("Chain-of-Thought Prompting Demo")
    print("=" * 60)

    # 1. Math problem
    print("\n1. Math Word Problem")
    print("-" * 60)

    problem = "Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 balls. How many balls does he have now?"
    result = await math_problem(problem)

    print(f"Problem: {problem}")
    print(f"\nReasoning:\n{result['reasoning']}")
    print(f"\nAnswer: {result['answer']}")
    print(f"Tokens: {result['tokens']}, Cost: ${result['cost']:.4f}\n")

    # 2. Logic puzzle
    print("\n2. Logic Puzzle")
    print("-" * 60)

    puzzle = "If all cats are mammals and some mammals swim, can we conclude that some cats swim?"
    result = await logic_puzzle(puzzle)

    print(f"Puzzle: {puzzle}")
    print(f"\nReasoning:\n{result['reasoning']}")
    print(f"Tokens: {result['tokens']}, Cost: ${result['cost']:.4f}\n")

    # 3. Multi-step planning
    print("\n3. Multi-Step Planning")
    print("-" * 60)

    result = await multi_step_planning(
        "Launch a new SaaS product",
        constraints=["Budget: $100k", "Timeline: 6 months", "Team: 5 people"]
    )

    print(f"Goal: {result['goal']}")
    print("\nPlan:")
    for i, step in enumerate(result['steps'], 1):
        print(f"{i}. {step}")
    print(f"\nTokens: {result['tokens']}, Cost: ${result['cost']:.4f}\n")

    # 4. CoT impact
    print("\n" + "=" * 60)
    print("Chain-of-Thought Impact")
    print("=" * 60)
    print("Math problems:")
    print("- Without CoT: ~60% accuracy")
    print("- With CoT: ~85-90% accuracy")
    print("\nCost: ~3-5x higher than zero-shot")
    print("Tokens: ~3-5x more (includes reasoning)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
