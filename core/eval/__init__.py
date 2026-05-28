"""
Evaluation primitives: LLM-as-judge, RAGAS metrics.

Design principles:
- LLM-as-judge for custom rubrics
- RAGAS integration (faithfulness, answer_relevancy, context_precision)
- Batch scoring
"""

import logging

from core.llm import chat
from core.schemas import EvalScore


logger = logging.getLogger(__name__)


async def judge(
    prediction: str,
    reference: str,
    rubric: str,
) -> EvalScore:
    """
    LLM-as-judge scoring.

    Args:
        prediction: Model output
        reference: Ground truth / reference answer
        rubric: Scoring rubric

    Returns:
        EvalScore with score (0-1) and reasoning

    Cost:
        ~$0.0005 USD per judgment (Haiku)
    """
    prompt = f"""You are an expert evaluator. Score the prediction against the reference using this rubric:

Rubric: {rubric}

Reference: {reference}

Prediction: {prediction}

Provide:
1. A score from 0.0 to 1.0 (where 1.0 is perfect)
2. Brief reasoning for the score

Format your response as:
Score: <number>
Reasoning: <explanation>
"""

    messages = [{"role": "user", "content": prompt}]
    response = await chat(messages, temperature=0.0)

    # Parse response
    try:
        lines = response.text.strip().split("\n")
        score_line = [l for l in lines if l.startswith("Score:")][0]
        reasoning_line = [l for l in lines if l.startswith("Reasoning:")][0]

        score = float(score_line.split(":")[-1].strip())
        reasoning = reasoning_line.split(":", 1)[-1].strip()

        return EvalScore(score=score, reasoning=reasoning, rubric=rubric)

    except Exception as e:
        logger.warning(f"Failed to parse judge response: {e}")
        return EvalScore(score=0.0, reasoning="Parse error", rubric=rubric)


async def faithfulness(response: str, context: str) -> float:
    """
    RAGAS: Is response faithful to context?

    Args:
        response: LLM response
        context: Retrieved context

    Returns:
        Score 0-1
    """
    rubric = "Is the response factually consistent with the context? Score 1.0 if all facts in response are supported by context, 0.0 if contradictory."
    result = await judge(prediction=response, reference=context, rubric=rubric)
    return result.score


async def answer_relevancy(response: str, query: str) -> float:
    """
    RAGAS: How well does response answer query?

    Args:
        response: LLM response
        query: User query

    Returns:
        Score 0-1
    """
    rubric = "How well does the response answer the query? Score 1.0 if fully answers, 0.0 if unrelated."
    result = await judge(prediction=response, reference=query, rubric=rubric)
    return result.score


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
    combined_context = "\n\n".join(context)
    rubric = "Is the context relevant to generating this response? Score 1.0 if all context chunks are useful, 0.0 if irrelevant."
    result = await judge(prediction=response, reference=combined_context, rubric=rubric)
    return result.score


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
