"""
Retry policies using Tenacity.

Design principles:
- Standard: exponential backoff, 3 retries, on 429/500/timeout
- Idempotent: only retry on safe-to-repeat errors
- LLM rate limit: long backoff for provider rate limits
"""

from typing import Callable, TypeVar

F = TypeVar("F")


def policy_standard() -> Callable[[Callable[..., F]], Callable[..., F]]:
    """
    Standard retry: exponential backoff, 3 attempts, on 429/500/timeout.

    Retries on:
    - 429 (rate limited)
    - 500–599 (server error)
    - Timeout

    Does NOT retry on:
    - 400, 401, 403 (client error)
    - 413 (payload too large)
    """
    raise NotImplementedError


def policy_idempotent() -> Callable[[Callable[..., F]], Callable[..., F]]:
    """
    Idempotent retry: only retry if safe to re-run.

    Only retries on:
    - 429 (rate limited)
    - 500–599 (server error)
    - Timeout

    Idempotent GET/read operations only.
    """
    raise NotImplementedError


def policy_llm_rate_limit() -> Callable[[Callable[..., F]], Callable[..., F]]:
    """
    LLM rate limit retry: long backoff for provider rate limits.

    On 429 from LLM provider:
    - Wait 2^attempt seconds (exp backoff)
    - Max 5 retries (~30 seconds total)
    """
    raise NotImplementedError
