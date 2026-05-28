"""Tests for core/config module."""

import pytest

from core.config import Settings, get_settings


def test_settings_defaults():
    """Test that settings have sensible defaults."""
    settings = Settings()

    assert settings.DEFAULT_LLM == "anthropic/claude-3-5-haiku-20241022"
    assert settings.FALLBACK_LLM == "openai/gpt-4o-mini"
    assert settings.ENABLE_CACHE is True
    assert settings.CACHE_TTL == 86400
    assert settings.SEMANTIC_CACHE_THRESHOLD == 0.93
    assert settings.ENVIRONMENT == "development"


def test_settings_singleton():
    """Test that get_settings returns singleton."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_is_production():
    """Test environment detection."""
    settings = Settings(ENVIRONMENT="production")
    assert settings.is_production() is True
    assert settings.is_development() is False


def test_is_development():
    """Test development detection."""
    settings = Settings(ENVIRONMENT="development")
    assert settings.is_development() is True
    assert settings.is_production() is False
