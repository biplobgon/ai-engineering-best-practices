"""
Core package: Shared primitives for all AI engineering modules.

This package provides the foundational layer that all other modules import.

Design philosophy:
- Single source of truth for LLM calls
- Automatic caching, retries, observability
- Type-safe with Pydantic
- Cost-optimized by default

Modules:
- llm: LLM client + router (LiteLLM wrapper)
- cache: Exact + semantic caching (Redis)
- schemas: Pydantic models + Instructor
- telemetry: OpenTelemetry + cost metrics
- retry: Tenacity policies
- prompts: Template loader + versioning
- eval: LLM-as-judge + RAGAS
- guardrails: Input/output validation
- config: Pydantic settings

Usage:
    >>> from core.llm import chat
    >>> from core.cache import semantic_cache
    >>> from core.config import settings
    >>>
    >>> response = await chat([{"role": "user", "content": "Hello"}])
    >>> print(response.text, f"${response.usd_cost}")
"""

__version__ = "0.1.0"
