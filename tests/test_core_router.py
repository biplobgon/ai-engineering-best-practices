"""Tests for core/llm/router module."""

import pytest

from core.llm.router import Router


def test_router_choose():
    """Test router model selection."""
    router = Router()

    # Classification should get cheap model
    model = router.choose("classification")
    assert "haiku" in model.lower() or "mini" in model.lower()

    # Reasoning should get smarter model
    model = router.choose("reasoning")
    assert "sonnet" in model.lower() or "gpt-4o" in model.lower()


def test_router_get_fallback():
    """Test fallback model selection."""
    router = Router()

    models = router.get_all_models("generation")
    if len(models) > 1:
        current = models[0]
        fallback = router.get_fallback("generation", current)
        assert fallback == models[1]


def test_router_get_all_models():
    """Test getting all models for a task."""
    router = Router()

    models = router.get_all_models("classification")
    assert len(models) > 0
    assert isinstance(models[0], str)
