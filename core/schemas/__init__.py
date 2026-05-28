"""
Pydantic schemas and Instructor wrappers for structured outputs.

Design principles:
- Pydantic v2 for validation + JSON schema generation
- Instructor for auto-retry on parse failure
- Type-safe, reusable models
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class Message(BaseModel):
    """Chat message."""

    role: str = Field(..., description="'user', 'assistant', 'system'")
    content: str = Field(..., description="Message text")
    name: Optional[str] = Field(None, description="Optional sender name")


class FunctionCall(BaseModel):
    """Function/tool call."""

    name: str = Field(..., description="Function name")
    arguments: dict[str, Any] = Field(..., description="Function arguments")


class ToolCall(BaseModel):
    """Tool call (OpenAI tools API)."""

    id: str = Field(..., description="Call ID")
    type: str = Field("function", description="Always 'function'")
    function: FunctionCall = Field(..., description="Function details")


class Response(BaseModel):
    """LLM response with metadata."""

    text: str = Field(..., description="Response text")
    tokens_in: int = Field(..., description="Input tokens")
    tokens_out: int = Field(..., description="Output tokens")
    usd_cost: float = Field(..., description="Cost in USD")
    latency_ms: float = Field(..., description="Latency in milliseconds")
    model: str = Field(..., description="Model used")
    cached: bool = Field(False, description="Was response cached?")
    finish_reason: str = Field(..., description="e.g., 'stop', 'length'")
    tool_calls: Optional[list[ToolCall]] = Field(None, description="If tool-calling")


class Citation(BaseModel):
    """Citation with source tracking."""

    text: str = Field(..., description="Cited text")
    source: str = Field(..., description="Source document ID or URL")
    page: Optional[int] = Field(None, description="Page number if applicable")
    confidence: float = Field(1.0, description="0-1 confidence in citation")


class TextWithCitations(BaseModel):
    """Text output with citations."""

    text: str = Field(..., description="Output text")
    citations: list[Citation] = Field(default_factory=list, description="Citations")
