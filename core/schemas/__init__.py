"""
Pydantic schemas and Instructor wrappers for structured outputs.

Design principles:
- Pydantic v2 for validation + JSON schema generation
- Instructor for auto-retry on parse failure
- Type-safe, reusable models
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    """Chat message."""

    role: Literal["user", "assistant", "system", "tool"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message text")
    name: str | None = Field(None, description="Optional sender name")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of allowed values."""
        if v not in {"user", "assistant", "system", "tool"}:
            raise ValueError(
                f"Invalid role: {v}. Must be 'user', 'assistant', 'system', or 'tool'"
            )
        return v


class FunctionCall(BaseModel):
    """Function/tool call."""

    name: str = Field(..., description="Function name")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Function arguments"
    )


class ToolCall(BaseModel):
    """Tool call (OpenAI tools API)."""

    id: str = Field(..., description="Call ID")
    type: Literal["function"] = Field(default="function", description="Always 'function'")
    function: FunctionCall = Field(..., description="Function details")


class TokenUsage(BaseModel):
    """Token usage metadata."""

    prompt_tokens: int = Field(..., description="Input tokens", ge=0)
    completion_tokens: int = Field(..., description="Output tokens", ge=0)
    total_tokens: int = Field(..., description="Total tokens", ge=0)

    @property
    def tokens_in(self) -> int:
        """Alias for prompt_tokens."""
        return self.prompt_tokens

    @property
    def tokens_out(self) -> int:
        """Alias for completion_tokens."""
        return self.completion_tokens


class LLMResponse(BaseModel):
    """LLM response with full metadata."""

    text: str = Field(..., description="Response text")
    tokens_in: int = Field(..., description="Input tokens", ge=0)
    tokens_out: int = Field(..., description="Output tokens", ge=0)
    usd_cost: float = Field(..., description="Cost in USD", ge=0.0)
    latency_ms: float = Field(..., description="Latency in milliseconds", ge=0.0)
    model: str = Field(..., description="Model used")
    cached: bool = Field(default=False, description="Was response cached?")
    finish_reason: str = Field(..., description="e.g., 'stop', 'length', 'content_filter'")
    tool_calls: list[ToolCall] | None = Field(None, description="If tool-calling")
    raw: dict[str, Any] | None = Field(None, description="Raw provider response")

    @property
    def total_tokens(self) -> int:
        """Total tokens (in + out)."""
        return self.tokens_in + self.tokens_out

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LLMResponse(text={self.text[:50]!r}..., "
            f"tokens={self.total_tokens}, cost=${self.usd_cost:.4f}, "
            f"latency={self.latency_ms:.0f}ms, cached={self.cached})"
        )


class Chunk(BaseModel):
    """Streaming chunk of LLM output."""

    content: str = Field(..., description="Chunk content")
    tokens: int = Field(default=0, description="Tokens in this chunk", ge=0)
    latency_ms: float = Field(default=0.0, description="Latency since stream start", ge=0.0)
    finish_reason: str | None = Field(None, description="If final chunk")

    def __repr__(self) -> str:
        """String representation."""
        return f"Chunk(content={self.content!r}, tokens={self.tokens})"


class Citation(BaseModel):
    """Citation with source tracking."""

    text: str = Field(..., description="Cited text")
    source: str = Field(..., description="Source document ID or URL")
    page: int | None = Field(None, description="Page number if applicable", ge=1)
    confidence: float = Field(default=1.0, description="0-1 confidence in citation", ge=0.0, le=1.0)


class TextWithCitations(BaseModel):
    """Text output with citations."""

    text: str = Field(..., description="Output text")
    citations: list[Citation] = Field(default_factory=list, description="Citations")

    @field_validator("citations")
    @classmethod
    def validate_citations(cls, v: list[Citation]) -> list[Citation]:
        """Ensure citations are unique by source."""
        seen = set()
        unique = []
        for citation in v:
            if citation.source not in seen:
                seen.add(citation.source)
                unique.append(citation)
        return unique


class EvalScore(BaseModel):
    """Evaluation score with reasoning."""

    score: float = Field(..., description="Score (0-1)", ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Explanation of score")
    rubric: str | None = Field(None, description="Rubric used for scoring")

    def __repr__(self) -> str:
        """String representation."""
        return f"EvalScore(score={self.score:.2f}, reasoning={self.reasoning[:50]!r}...)"


# Convenience type aliases
Response = LLMResponse  # Backward compatibility
