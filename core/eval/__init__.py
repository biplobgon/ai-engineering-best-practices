"""
Evaluation primitives: LLM-as-judge, RAGAS metrics.

Design principles:
- LLM-as-judge for custom rubrics
- RAGAS integration (faithfulness, answer_relevancy, context_precision)
- Batch scoring
"""

from typing import Optional


async def judge(
    prediction: str,
    reference: str,
    rubric: str,
) -> dict[str, float]:
    """
    LLM-as-judge scoring.

    Args:
        prediction: Model output
        reference: Ground truth / reference answer
        rubric: Scoring rubric (e.g., "Is output faithful to context?")

    Returns:
        Dict with 'score' (0-1) and 'reasoning' (explanation)

    Cost:
        ~0.0005 USD per judgment (Haiku)
    """
    raise NotImplementedError


async def faithfulness(response: str, context: str) -> float:
    """
    RAGAS: Is response faithful to context?

    Args:
        response: LLM response
        context: Retrieved context

    Returns:
        Score 0-1
    """
    raise NotImplementedError


async def answer_relevancy(response: str, query: str) -> float:
    """
    RAGAS: How well does response answer query?

    Args:
        response: LLM response
        query: User query

    Returns:
        Score 0-1
    """
    raise NotImplementedError


async def context_precision(
    response: str,
    context: list[str],
) -> float:
    """
    RAGAS: Is context relevant to response?

    Args:
        response: LLM response
        context: List of context chunks

    Returns:
        Score 0-1
    """
    raise NotImplementedError
