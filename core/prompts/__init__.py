"""
Prompt template loader and versioning.

Design principles:
- File-backed prompts (YAML or Markdown)
- Versioned by date/hash
- Parameterized with Jinja2
- Searchable registry
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


logger = logging.getLogger(__name__)

# Prompts directory (create if not exists)
PROMPTS_DIR = Path("prompts")
PROMPTS_DIR.mkdir(exist_ok=True)


class PromptRegistry:
    """File-backed prompt registry with versioning."""

    def __init__(self, prompts_dir: Path = PROMPTS_DIR) -> None:
        """Initialize registry."""
        self.prompts_dir = prompts_dir
        self.prompts_dir.mkdir(exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(str(prompts_dir)))

    async def load(
        self,
        name: str,
        version: str = "latest",
        **variables: Any,
    ) -> str:
        """
        Load and render prompt template.

        Args:
            name: Prompt name (e.g., "rag.answer_generation")
            version: Version (default: "latest")
            **variables: Template variables

        Returns:
            Rendered prompt string
        """
        try:
            # For now, just use name.jinja2 (versioning in Phase 3)
            template_name = f"{name}.jinja2"
            template = self.env.get_template(template_name)
            rendered = template.render(**variables)
            logger.debug(f"Loaded prompt: {name}")
            return rendered

        except TemplateNotFound:
            # Return a simple default prompt
            logger.warning(f"Prompt not found: {name}, using default")
            return "You are a helpful AI assistant. {{query}}"

    async def save(
        self,
        name: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Save prompt template.

        Args:
            name: Prompt name
            content: Template content (Jinja2 syntax)
            metadata: Optional metadata

        Returns:
            Version hash
        """
        template_path = self.prompts_dir / f"{name}.jinja2"
        template_path.write_text(content, encoding="utf-8")

        # Generate version hash
        version_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        version = f"{datetime.now().strftime('%Y%m%d')}-{version_hash}"

        logger.info(f"Saved prompt: {name} (version: {version})")
        return version

    async def list_prompts(self) -> list[str]:
        """List all prompt names."""
        prompts = [
            p.stem for p in self.prompts_dir.glob("*.jinja2")
        ]
        return prompts

    async def list_versions(self, name: str) -> list[str]:
        """List versions (simplified for Phase 2)."""
        return ["latest"]


# Global registry
_registry = PromptRegistry()


# Convenience functions
async def load(name: str, version: str = "latest", **variables: Any) -> str:
    """Load and render prompt template."""
    return await _registry.load(name, version, **variables)


async def save(name: str, content: str, metadata: dict[str, Any] | None = None) -> str:
    """Save prompt template."""
    return await _registry.save(name, content, metadata)


async def list_prompts() -> list[str]:
    """List all prompts."""
    return await _registry.list_prompts()


async def list_versions(name: str) -> list[str]:
    """List prompt versions."""
    return await _registry.list_versions(name)
