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

from core.llm.client import chat, embed, stream
from core.llm.router import Router, router


__all__ = [
    "chat",
    "stream",
    "embed",
    "router",
    "Router",
]
