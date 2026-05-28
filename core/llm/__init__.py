"""
Core LLM client interface using LiteLLM.

This module provides a unified, async-native interface for LLM calls across
OpenAI, Anthropic, Bedrock, Ollama, and other providers via LiteLLM.

Design principles:
- Single source of truth for LLM access
- Automatic token/cost accounting
- Built-in caching (exact + semantic)
- OpenTelemetry instrumentation
- Automatic retry with exponential backoff
- Type-safe with Pydantic schemas
"""

from typing import AsyncIterator, Optional, Any, TypeVar

T = TypeVar("T")


class Response:
    """LLM response with metadata."""

    text: str
    tokens_in: int
    tokens_out: int
    usd_cost: float
    latency_ms: float
    model: str
    cached: bool
    finish_reason: str
    raw: dict[str, Any]

    def __repr__(self) -> str:
        raise NotImplementedError


class Chunk:
    """Streaming chunk of LLM output."""

    content: str
    tokens: int
    latency_ms: float

    def __repr__(self) -> str:
        raise NotImplementedError


class Router:
    """Model router for cost optimization (cheap-first)."""

    def choose(self, task_type: str) -> str:
        """
        Choose best model for task.

        Args:
            task_type: "classification", "reasoning", "generation", etc.

        Returns:
            Model name (e.g., "anthropic/claude-3-5-haiku-20241022")
        """
        raise NotImplementedError


async def chat(
    messages: list[dict[str, str]],
    *,
    model: Optional[str] = None,
    schema: Optional[type[T]] = None,
    cache: bool = True,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    stop: Optional[list[str]] = None,
    **kwargs,
) -> Response:
    """
    High-level chat interface with caching, retries, observability.

    Args:
        messages: List of {role, content} dicts
        model: Model name (defaults to config DEFAULT_LLM)
        schema: Pydantic model for structured output (enables Instructor)
        cache: Check exact + semantic cache before calling LLM
        temperature: Sampling temperature [0, 2]
        max_tokens: Max output tokens
        top_p: Nucleus sampling [0, 1]
        frequency_penalty: Repetition penalty [-2, 2]
        presence_penalty: Presence penalty [-2, 2]
        stop: Stop sequences
        **kwargs: Provider-specific kwargs

    Returns:
        Response with text, tokens_in, tokens_out, usd_cost, latency_ms, cached

    Raises:
        ValueError: If messages format invalid
        RateLimitError: If API rate limited (auto-retry)
        TokenLimitError: If tokens exceed context window
        ValidationError: If schema validation fails (auto-retry with Instructor)

    Cost:
        ~$0.0001 USD (Haiku), less if cached.

    Example:
        >>> response = await chat([{"role": "user", "content": "Hello"}])
        >>> print(response.text, f"${response.usd_cost}")
    """
    raise NotImplementedError


async def stream(
    messages: list[dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> AsyncIterator[Chunk]:
    """
    Token-by-token streaming for low-latency apps.

    Args:
        messages: Same as chat()
        model: Same as chat()
        temperature: Same as chat()
        max_tokens: Same as chat()
        **kwargs: Provider-specific kwargs

    Yields:
        Chunk with content, tokens, latency_ms

    Cost:
        Same as chat() but spread across multiple chunks.

    Example:
        >>> async for chunk in stream([...]):
        >>>     print(chunk.content, end="", flush=True)
    """
    raise NotImplementedError


async def embed(
    texts: list[str],
    model: Optional[str] = None,
    batch_size: int = 1000,
) -> list[list[float]]:
    """
    Batch embedding with automatic batching and caching.

    Args:
        texts: List of texts to embed
        model: Embedding model (defaults to config EMBED_MODEL)
        batch_size: Process N texts concurrently

    Returns:
        List of embedding vectors (dim depends on model)

    Cost:
        ~$0.02 per 1M tokens (Anthropic, with semantic cache possible)

    Example:
        >>> embeddings = await embed(["Hello", "World"])
        >>> len(embeddings[0])  # e.g., 1536 for OpenAI
    """
    raise NotImplementedError


router: Router = Router()
"""Global router instance for model selection."""
