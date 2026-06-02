"""
Tests for token counting functionality.
"""

import pytest
from fundamentals.fundamentals_01_llm_basics.token_counting import (
    count_tokens,
    check_token_budget,
    validate_request,
    truncate_to_budget,
)


def test_count_tokens_basic():
    """Test basic token counting."""
    text = "Hello, world!"
    count = count_tokens(text, model="gpt-4")
    
    # "Hello, world!" is typically 4-5 tokens
    assert 3 <= count <= 6


def test_count_tokens_empty():
    """Test token counting with empty string."""
    count = count_tokens("", model="gpt-4")
    assert count == 0


def test_count_tokens_long():
    """Test token counting with longer text."""
    text = "The quick brown fox jumps over the lazy dog. " * 100
    count = count_tokens(text, model="gpt-4")
    
    # Should be roughly 900-1100 tokens
    assert 800 <= count <= 1200


def test_check_token_budget_within():
    """Test budget check for text within limits."""
    text = "Hello, world!"
    result = check_token_budget(text, model="gpt-4", expected_output_tokens=100)
    
    assert result.within_budget is True
    assert result.count > 0
    assert result.estimated_cost_usd > 0
    assert result.estimated_latency_sec > 0


def test_check_token_budget_exceeds():
    """Test budget check for text exceeding limits."""
    # Create very long text
    text = "word " * 200_000  # Way over 128K tokens
    result = check_token_budget(text, model="gpt-4", expected_output_tokens=100)
    
    assert result.within_budget is False


def test_validate_request_valid():
    """Test request validation with valid input."""
    text = "Hello, world!"
    valid, message = validate_request(
        text,
        model="gpt-4",
        max_cost_usd=1.0,
        max_latency_sec=10.0,
    )
    
    assert valid is True
    assert "✅" in message


def test_validate_request_cost_exceeded():
    """Test request validation with cost limit exceeded."""
    text = "word " * 10_000  # High token count
    valid, message = validate_request(
        text,
        model="gpt-4",
        max_cost_usd=0.0001,  # Very low budget
        max_latency_sec=100.0,
    )
    
    assert valid is False
    assert "cost" in message.lower()


def test_truncate_to_budget_no_truncation():
    """Test truncation when text is within budget."""
    text = "Hello, world!"
    result = truncate_to_budget(text, max_tokens=100, model="gpt-4")
    
    # Should not be truncated
    assert result == text
    assert "[truncated]" not in result


def test_truncate_to_budget_with_truncation():
    """Test truncation when text exceeds budget."""
    text = "word " * 1000
    result = truncate_to_budget(text, max_tokens=50, model="gpt-4")
    
    # Should be truncated
    assert len(result) < len(text)
    assert "[truncated]" in result
    
    # Verify truncated text is within budget
    count = count_tokens(result, model="gpt-4")
    assert count <= 55  # Allow small buffer


def test_token_ratio_english():
    """Test that English text has expected token ratio."""
    text = "The quick brown fox jumps over the lazy dog. " * 20
    
    chars = len(text)
    tokens = count_tokens(text, model="gpt-4")
    words = len(text.split())
    
    # Rule of thumb: 1 token ≈ 4 chars
    chars_per_token = chars / tokens
    assert 3.0 <= chars_per_token <= 5.0
    
    # Rule of thumb: 1 token ≈ 0.75 words (or 1.33 tokens/word)
    tokens_per_word = tokens / words
    assert 1.0 <= tokens_per_word <= 1.6
