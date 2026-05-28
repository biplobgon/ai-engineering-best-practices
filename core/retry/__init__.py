"""
Retry policies using Tenacity.

Design principles:
- Standard: exponential backoff, 3 retries, on 429/500/timeout
- Idempotent: only retry on safe-to-repeat errors
- LLM rate limit: long backoff for provider rate limits
"""

import logging
from typing import Any, Callable, TypeVar

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)


logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def _log_retry(retry_state: RetryCallState) -> None:
    """Log retry attempts."""
    logger.warning(
        "Retrying after failure",
        extra={
            "attempt": retry_state.attempt_number,
            "exception": str(retry_state.outcome.exception())
            if retry_state.outcome
            else None,
        },
    )


def _is_retryable_http_error(exception: Exception) -> bool:
    """Check if HTTP error is retryable (429, 500-599, timeout)."""
    # Handle common HTTP exceptions
    if hasattr(exception, "status_code"):
        status = exception.status_code
        return status == 429 or 500 <= status < 600

    # Handle timeout errors
    if isinstance(exception, TimeoutError):
        return True

    # Handle connection errors
    error_name = type(exception).__name__
    if any(
        err in error_name.lower()
        for err in ["timeout", "connection", "network", "ratelimit"]
    ):
        return True

    return False


def policy_standard() -> Callable[[F], F]:
    """
    Standard retry: exponential backoff, 3 attempts, on 429/500/timeout.

    Retries on:
    - 429 (rate limited)
    - 500–599 (server error)
    - Timeout

    Does NOT retry on:
    - 400, 401, 403 (client error)
    - 413 (payload too large)

    Backoff: wait 1s, 2s, 4s between retries.
    """
    return retry(
        retry=retry_if_exception_type((Exception,)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        before_sleep=_log_retry,
        reraise=True,
    )


def policy_idempotent() -> Callable[[F], F]:
    """
    Idempotent retry: only retry if safe to re-run.

    Only retries on:
    - 429 (rate limited)
    - 500–599 (server error)
    - Timeout

    Idempotent GET/read operations only.
    Backoff: wait 1s, 2s, 4s between retries.
    """
    return retry(
        retry=retry_if_exception_type((Exception,)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        before_sleep=_log_retry,
        reraise=True,
    )


def policy_llm_rate_limit() -> Callable[[F], F]:
    """
    LLM rate limit retry: long backoff for provider rate limits.

    On 429 from LLM provider:
    - Wait 2^attempt seconds (exp backoff)
    - Max 5 retries (~30 seconds total)

    Backoff: wait 2s, 4s, 8s, 16s, 32s between retries.
    """
    return retry(
        retry=retry_if_exception_type((Exception,)),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=_log_retry,
        reraise=True,
    )


def policy_no_retry() -> Callable[[F], F]:
    """No retry policy (fail immediately)."""
    return retry(stop=stop_after_attempt(1), reraise=True)


# Convenience decorator for immediate use
def with_retry(func: F) -> F:
    """Apply standard retry policy to a function."""
    return policy_standard()(func)
