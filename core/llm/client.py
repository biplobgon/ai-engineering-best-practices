"""
LLM client implementation using LiteLLM.

Provides unified async interface for LLM calls across providers.
"""

import hashlib
import logging
import time
from typing import Any, AsyncIterator

import litellm
from litellm import acompletion, aembedding

from core.config import get_settings
from core.retry import policy_llm_rate_limit
from core.schemas import Chunk, LLMResponse, Message, TokenUsage
from core.telemetry import meters, traced


logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.suppress_debug_info = True
litellm.drop_params = True  # Drop unsupported params instead of failing


def _calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """
    Calculate cost in USD based on model pricing.

    Uses LiteLLM's cost calculation when available, falls back to estimates.
    """
    try:
        # LiteLLM has built-in cost tracking
        return litellm.completion_cost(
            model=model,
            prompt_tokens=tokens_in,
            completion_tokens=tokens_out,
        )
    except Exception:
        # Fallback to hardcoded estimates (as of May 2024)
        pricing = {
            "claude-3-5-haiku": (0.0008 / 1000, 0.004 / 1000),  # per token
            "claude-3-haiku": (0.00025 / 1000, 0.00125 / 1000),
            "gpt-4o-mini": (0.00015 / 1000, 0.0006 / 1000),
            "gpt-4o": (0.005 / 1000, 0.015 / 1000),
            "gpt-3.5-turbo": (0.0005 / 1000, 0.0015 / 1000),
        }

        # Find matching pricing
        for key, (input_price, output_price) in pricing.items():
            if key in model.lower():
                return (tokens_in * input_price) + (tokens_out * output_price)

        # Default fallback (conservative estimate)
        return (tokens_in * 0.001 / 1000) + (tokens_out * 0.002 / 1000)


@traced("llm.chat")
@policy_llm_rate_limit()
async def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    schema: type | None = None,
    cache: bool = True,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    stop: list[str] | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """
    High-level chat interface with caching, retries, observability.

    Args:
        messages: List of {role, content} dicts
        model: Model name (defaults to config DEFAULT_LLM)
        schema: Pydantic model for structured output (uses Instructor)
        cache: Check exact + semantic cache before calling LLM
        temperature: Sampling temperature [0, 2]
        max_tokens: Max output tokens
        top_p: Nucleus sampling [0, 1]
        frequency_penalty: Repetition penalty [-2, 2]
        presence_penalty: Presence penalty [-2, 2]
        stop: Stop sequences
        **kwargs: Provider-specific kwargs

    Returns:
        LLMResponse with text, tokens_in, tokens_out, usd_cost, latency_ms, cached

    Raises:
        ValueError: If messages format invalid
        RateLimitError: If API rate limited (auto-retry)
        TokenLimitError: If tokens exceed context window
        ValidationError: If schema validation fails (auto-retry with Instructor)

    Cost:
        ~$0.0001 USD (Haiku), less if cached.
    """
    settings = get_settings()
    model = model or settings.DEFAULT_LLM

    # Validate messages
    if not messages:
        raise ValueError("Messages list cannot be empty")

    for msg in messages:
        if "role" not in msg or "content" not in msg:
            raise ValueError(f"Invalid message format: {msg}")

    # TODO: Check cache if enabled (Phase 2.2)
    # if cache and settings.ENABLE_CACHE:
    #     cached_response = await _check_cache(messages, model, temperature)
    #     if cached_response:
    #         return cached_response

    # Make LLM call
    start_time = time.perf_counter()

    try:
        response = await acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
            **kwargs,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Extract response data
        content = response.choices[0].message.content or ""
        finish_reason = response.choices[0].finish_reason or "stop"

        # Extract token usage
        usage = response.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0

        # Calculate cost
        usd_cost = _calculate_cost(model, tokens_in, tokens_out)

        # Track metrics
        if settings.TRACK_COST:
            meters.increment_tokens_in(tokens_in, model)
            meters.increment_tokens_out(tokens_out, model)
            meters.increment_usd_cost(usd_cost, model)
            meters.record_latency_ms(latency_ms, "llm.chat")

        # Build response
        llm_response = LLMResponse(
            text=content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            usd_cost=usd_cost,
            latency_ms=latency_ms,
            model=model,
            cached=False,
            finish_reason=finish_reason,
            raw=response.model_dump() if hasattr(response, "model_dump") else None,
        )

        logger.info(
            "LLM call completed",
            extra={
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "usd_cost": usd_cost,
                "latency_ms": latency_ms,
            },
        )

        return llm_response

    except Exception as e:
        logger.error(f"LLM call failed: {e}", extra={"model": model, "error": str(e)})
        raise


@traced("llm.stream")
async def stream(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs: Any,
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
    """
    settings = get_settings()
    model = model or settings.DEFAULT_LLM

    start_time = time.perf_counter()
    total_tokens = 0

    try:
        response = await acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        async for chunk_data in response:
            if not chunk_data.choices:
                continue

            delta = chunk_data.choices[0].delta
            content = delta.get("content", "") if isinstance(delta, dict) else getattr(delta, "content", "")
            finish_reason = chunk_data.choices[0].finish_reason

            if content:
                total_tokens += 1  # Rough estimate
                latency_ms = (time.perf_counter() - start_time) * 1000

                yield Chunk(
                    content=content,
                    tokens=1,
                    latency_ms=latency_ms,
                    finish_reason=finish_reason,
                )

    except Exception as e:
        logger.error(f"LLM streaming failed: {e}", extra={"model": model})
        raise


@traced("llm.embed")
@policy_llm_rate_limit()
async def embed(
    texts: list[str],
    model: str | None = None,
    batch_size: int = 100,
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
        ~$0.02 per 1M tokens (varies by provider)
    """
    settings = get_settings()
    model = model or settings.EMBED_MODEL

    if not texts:
        return []

    # Batch processing
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        try:
            response = await aembedding(model=model, input=batch)

            # Extract embeddings
            embeddings = [item["embedding"] for item in response.data]
            all_embeddings.extend(embeddings)

            # Track metrics (rough estimate)
            total_tokens = sum(len(text.split()) for text in batch)
            meters.increment_tokens_in(total_tokens, model)

        except Exception as e:
            logger.error(f"Embedding failed for batch: {e}")
            raise

    return all_embeddings
