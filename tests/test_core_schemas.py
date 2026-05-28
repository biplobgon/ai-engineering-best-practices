"""Tests for core/schemas module."""

import pytest
from pydantic import ValidationError

from core.schemas import (
    Chunk,
    Citation,
    EvalScore,
    LLMResponse,
    Message,
    TextWithCitations,
    TokenUsage,
)


def test_message_validation():
    """Test Message model validation."""
    # Valid message
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"

    # Invalid role should fail
    with pytest.raises(ValidationError):
        Message(role="invalid", content="test")


def test_llm_response():
    """Test LLMResponse model."""
    response = LLMResponse(
        text="Hello world",
        tokens_in=10,
        tokens_out=5,
        usd_cost=0.0001,
        latency_ms=100.5,
        model="test-model",
        finish_reason="stop",
    )

    assert response.text == "Hello world"
    assert response.total_tokens == 15
    assert response.cached is False
    assert "Hello world" in repr(response)


def test_chunk():
    """Test Chunk model."""
    chunk = Chunk(content="test", tokens=1, latency_ms=10.0)
    assert chunk.content == "test"
    assert "test" in repr(chunk)


def test_citation():
    """Test Citation model."""
    citation = Citation(text="Quote", source="doc1", page=5, confidence=0.9)
    assert citation.text == "Quote"
    assert citation.page == 5
    assert citation.confidence == 0.9


def test_text_with_citations():
    """Test TextWithCitations with deduplication."""
    text_with_cit = TextWithCitations(
        text="Response",
        citations=[
            Citation(text="A", source="doc1"),
            Citation(text="B", source="doc1"),  # Duplicate source
            Citation(text="C", source="doc2"),
        ],
    )

    # Should deduplicate by source
    assert len(text_with_cit.citations) == 2


def test_eval_score():
    """Test EvalScore model."""
    score = EvalScore(score=0.85, reasoning="Good quality")
    assert score.score == 0.85
    assert "0.85" in repr(score)

    # Score must be 0-1
    with pytest.raises(ValidationError):
        EvalScore(score=1.5, reasoning="Invalid")
