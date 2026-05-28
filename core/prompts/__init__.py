"""
Prompt template loader and versioning.

Design principles:
- File-backed prompts (YAML or Markdown)
- Versioned by date/hash
- Parameterized with Jinja2
- Searchable registry
"""

from typing import Optional, Any


async def load(
    name: str,
    version: str = "latest",
    **variables: Any,
) -> str:
    """
    Load prompt template by name and version.

    Args:
        name: Prompt name (e.g., "rag.answer_generation")
        version: Version string (e.g., "2024-05-28" or "latest")
        **variables: Template variables (e.g., context="...", query="...")

    Returns:
        Rendered prompt string

    Raises:
        ValueError: If prompt or version not found
        TemplateError: If template rendering fails

    Example:
        >>> prompt = await load("rag.answer_generation", 
        ...                      version="latest",
        ...                      context="The sky is blue",
        ...                      query="What color is the sky?")
        >>> # Returns rendered prompt with context + query inserted
    """
    raise NotImplementedError


async def save(
    name: str,
    content: str,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """
    Save new prompt version.

    Args:
        name: Prompt name
        content: Prompt text (may include Jinja2 templates)
        metadata: Optional metadata (author, description, etc.)

    Returns:
        Version string (e.g., "2024-05-28-abc123def")
    """
    raise NotImplementedError


async def list_prompts() -> list[str]:
    """List all prompt names."""
    raise NotImplementedError


async def list_versions(name: str) -> list[str]:
    """List all versions of a prompt."""
    raise NotImplementedError
