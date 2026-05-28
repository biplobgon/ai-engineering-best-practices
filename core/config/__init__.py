"""
Configuration: Pydantic settings from .env.

Design principles:
- Single source of environment configuration
- Type-safe validation on load
- Sensible defaults
"""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration from .env."""

    # LLM Configuration
    DEFAULT_LLM: str = Field(
        default="anthropic/claude-3-5-haiku-20241022",
        description="Default LLM model (cheap-first routing)",
    )
    FALLBACK_LLM: str = Field(
        default="openai/gpt-4o-mini", description="Fallback LLM model"
    )
    EMBED_MODEL: str = Field(
        default="text-embedding-3-small", description="Default embedding model"
    )

    # API Keys
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")

    # Cache Configuration
    ENABLE_CACHE: bool = Field(default=True, description="Enable caching globally")
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    CACHE_TTL: int = Field(default=86400, description="Cache TTL in seconds (1 day)")
    SEMANTIC_CACHE_THRESHOLD: float = Field(
        default=0.93,
        ge=0.0,
        le=1.0,
        description="Semantic cache cosine similarity threshold",
    )

    # Database Configuration
    POSTGRES_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/aiengineer",
        description="PostgreSQL connection URL",
    )

    # Observability
    JAEGER_AGENT_HOST: str = Field(
        default="localhost", description="Jaeger agent host"
    )
    JAEGER_AGENT_PORT: int = Field(default=6831, description="Jaeger agent port")
    ENABLE_TRACING: bool = Field(
        default=True, description="Enable OpenTelemetry tracing"
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    LOG_FORMAT: Literal["json", "console"] = Field(
        default="json", description="Log format (json for production, console for dev)"
    )

    # Application
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development", description="Application environment"
    )
    SERVICE_NAME: str = Field(
        default="ai-engineering-best-practices", description="Service name for tracing"
    )

    # Cost tracking
    TRACK_COST: bool = Field(
        default=True, description="Track token usage and cost metrics"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars
    )

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"


# Global settings instance (lazy-loaded)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience export
settings = get_settings()
