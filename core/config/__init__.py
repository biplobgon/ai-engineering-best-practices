"""
Configuration: Pydantic settings from .env.

Design principles:
- Single source of environment configuration
- Type-safe validation on load
- Sensible defaults
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from .env."""

    # LLM Configuration
    DEFAULT_LLM: str = "anthropic/claude-3-5-haiku-20241022"
    FALLBACK_LLM: str = "openai/gpt-4o-mini"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Cache Configuration
    ENABLE_CACHE: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 86400
    SEMANTIC_CACHE_THRESHOLD: float = 0.93

    # Database Configuration
    POSTGRES_URL: str = "postgresql://postgres:postgres@localhost:5432/aiengineer"

    # Observability
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831
    LOG_LEVEL: str = "INFO"

    # Application
    ENVIRONMENT: str = "development"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
