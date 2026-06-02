"""
Tests for token reduction.

Run with: pytest prompt-engineering/optimization/tests/ -v
"""

import pytest

from prompt_engineering.optimization import token_reduction


class TestTokenReduction:
    """Test token reduction functions."""

    def test_remove_filler_words(self):
        """Test filler word removal."""
        text = "Please kindly analyze this text very carefully"
        result = token_reduction.remove_filler_words(text)

        assert "please" not in result.lower()
        assert "kindly" not in result.lower()
        assert "very" not in result.lower()
        assert "analyze" in result.lower()

    def test_remove_redundancy(self):
        """Test redundancy removal."""
        text = "In order to analyze this"
        result = token_reduction.remove_redundancy(text)

        assert "To analyze" in result or "to analyze" in result
        assert "in order" not in result.lower()

    def test_remove_greetings(self):
        """Test greeting removal."""
        text = "Hello! Please analyze this text. Thank you!"
        result = token_reduction.remove_greetings(text)

        assert "hello" not in result.lower()
        assert "thank" not in result.lower()
        assert "analyze" in result.lower()

    def test_compress(self):
        """Test full compression."""
        text = "Please kindly analyze and examine this text very carefully"
        result = token_reduction.compress(text, target_reduction=0.3)

        # Should be shorter
        assert len(result.split()) < len(text.split())

        # Should preserve key words
        assert "analyze" in result.lower() or "examine" in result.lower()

    def test_compress_preserves_meaning(self):
        """Test that compression preserves meaning."""
        text = "Classify the sentiment as Positive or Negative"
        result = token_reduction.compress(text, target_reduction=0.2)

        # Key terms should be preserved
        assert "classify" in result.lower() or "sentiment" in result.lower()

    def test_benchmark(self):
        """Test benchmark function."""
        text = "Please kindly analyze this text very carefully"
        results = token_reduction.benchmark(text)

        assert "original_words" in results
        assert "techniques" in results
        assert results["original_words"] > 0


@pytest.mark.asyncio
class TestTokenReductionAsync:
    """Test async token reduction functions."""

    async def test_compress_with_llm(self):
        """Test LLM-based compression."""
        text = "This is a long prompt that needs to be compressed to save tokens and reduce costs."
        result = await token_reduction.compress_with_llm(text, target_tokens=10)

        assert len(result) > 0
        assert len(result) < len(text)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
