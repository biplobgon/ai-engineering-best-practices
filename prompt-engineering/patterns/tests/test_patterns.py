"""
Tests for prompt patterns.

Run with: pytest prompt-engineering/patterns/tests/test_patterns.py -v
"""

import pytest

from prompt_engineering.patterns import (
    chain_of_thought,
    few_shot,
    zero_shot,
)


@pytest.mark.asyncio
class TestZeroShot:
    """Test zero-shot prompting."""

    async def test_basic_query(self):
        """Test basic zero-shot query."""
        result = await zero_shot.run(
            "What is 2+2?",
            instruction="Solve the math problem."
        )

        assert result is not None
        assert result.total_tokens > 0
        assert result.usd_cost >= 0

    async def test_sentiment_analysis(self):
        """Test sentiment classification."""
        result = await zero_shot.sentiment_analysis("I love this!")

        assert result in ["Positive", "Negative", "Neutral"]

    async def test_summarize(self):
        """Test summarization."""
        text = "This is a long text that needs to be summarized."
        summary = await zero_shot.summarize(text, max_words=10)

        assert len(summary) > 0
        assert len(summary.split()) <= 15  # Allow some flexibility


@pytest.mark.asyncio
class TestFewShot:
    """Test few-shot prompting."""

    async def test_with_examples(self):
        """Test few-shot with examples."""
        examples = [
            {"input": "I love it!", "output": "Positive"},
            {"input": "Terrible.", "output": "Negative"},
        ]

        result = await few_shot.run(
            "It's great!",
            examples=examples
        )

        assert result is not None
        assert result.total_tokens > 0

    async def test_sentiment_with_examples(self):
        """Test sentiment with few-shot."""
        sentiment = await few_shot.sentiment_analysis("This is amazing!")

        assert sentiment in ["Positive", "Negative", "Neutral"]

    async def test_style_transfer(self):
        """Test style transfer."""
        casual = "Hey what's up?"
        formal = await few_shot.style_transfer(casual, target_style="formal")

        assert len(formal) > 0
        assert formal != casual


@pytest.mark.asyncio
class TestChainOfThought:
    """Test chain-of-thought prompting."""

    async def test_math_problem(self):
        """Test math problem solving."""
        problem = "If Alice has 5 apples and gives 2 away, how many does she have?"
        result = await chain_of_thought.math_problem(problem)

        assert "reasoning" in result
        assert "answer" in result
        assert result["tokens"] > 0

    async def test_logic_puzzle(self):
        """Test logic puzzle."""
        puzzle = "If all A are B, and all B are C, are all A also C?"
        result = await chain_of_thought.logic_puzzle(puzzle)

        assert "reasoning" in result
        assert len(result["reasoning"]) > 0

    async def test_multi_step_planning(self):
        """Test multi-step planning."""
        result = await chain_of_thought.multi_step_planning(
            "Plan a birthday party",
            constraints=["Budget: $500", "Guests: 20"]
        )

        assert "steps" in result
        assert len(result["steps"]) > 0


@pytest.mark.asyncio
class TestPatternComparison:
    """Compare patterns on same task."""

    async def test_cost_comparison(self):
        """Compare costs across patterns."""
        query = "Classify: 'I love this product!'"

        # Zero-shot
        zero_result = await zero_shot.run(query)

        # Few-shot
        examples = [{"input": "Great!", "output": "Positive"}]
        few_result = await few_shot.run(query, examples=examples)

        # CoT (math-specific, use general run)
        cot_result = await chain_of_thought.run(query)

        # Few-shot should use more tokens than zero-shot
        assert few_result.total_tokens > zero_result.total_tokens

        # CoT should use most tokens (includes reasoning)
        assert cot_result.total_tokens >= zero_result.total_tokens


@pytest.mark.asyncio
class TestTokenAccounting:
    """Test token and cost tracking."""

    async def test_response_has_metadata(self):
        """Ensure responses have metadata."""
        result = await zero_shot.run("Test query")

        assert hasattr(result, "tokens_in")
        assert hasattr(result, "tokens_out")
        assert hasattr(result, "total_tokens")
        assert hasattr(result, "usd_cost")
        assert hasattr(result, "latency_ms")
        assert hasattr(result, "model")

    async def test_cost_calculation(self):
        """Test cost calculation."""
        result = await zero_shot.run("Short query")

        # Cost should be positive and reasonable
        assert result.usd_cost >= 0
        assert result.usd_cost < 0.01  # Should be very cheap for short query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
