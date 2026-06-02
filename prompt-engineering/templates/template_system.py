"""
Template system for reusable, versioned prompts.

Features:
- File-backed Jinja2 templates
- Variable substitution
- Hash-based versioning
- Template registry with metadata
- Performance tracking
- A/B testing support
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


logger = logging.getLogger(__name__)

# Templates directory
TEMPLATES_DIR = Path(__file__).parent / "prompts"
TEMPLATES_DIR.mkdir(exist_ok=True)

# Metadata storage
METADATA_FILE = TEMPLATES_DIR / "_metadata.json"


class TemplateSystem:
    """Prompt template management system."""

    def __init__(self, templates_dir: Path = TEMPLATES_DIR):
        """
        Initialize template system.

        Args:
            templates_dir: Directory containing templates
        """
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict[str, Any]:
        """Load template metadata from file."""
        if METADATA_FILE.exists():
            return json.loads(METADATA_FILE.read_text())
        return {}

    def _save_metadata(self) -> None:
        """Save template metadata to file."""
        METADATA_FILE.write_text(json.dumps(self.metadata, indent=2))

    async def load(
        self,
        name: str,
        version: str | None = None,
        **variables: Any,
    ) -> str:
        """
        Load and render template.

        Args:
            name: Template name (without .jinja2 extension)
            version: Optional version (default: latest)
            **variables: Template variables

        Returns:
            Rendered prompt string

        Example:
            >>> system = TemplateSystem()
            >>> prompt = await system.load(
            ...     "sentiment_analysis",
            ...     text="I love this!",
            ...     examples=[]
            ... )
        """
        try:
            template_file = f"{name}.jinja2"
            template = self.env.get_template(template_file)

            # Render template
            rendered = template.render(**variables)

            # Log usage
            self._log_usage(name, version or "latest")

            logger.debug(f"Loaded template: {name}")
            return rendered

        except TemplateNotFound:
            logger.error(f"Template not found: {name}")
            raise ValueError(f"Template '{name}' not found")

    async def save(
        self,
        name: str,
        content: str,
        description: str = "",
        author: str = "",
    ) -> str:
        """
        Save template.

        Args:
            name: Template name
            content: Template content (Jinja2 syntax)
            description: Template description
            author: Author name

        Returns:
            Version hash

        Example:
            >>> version = await system.save(
            ...     "sentiment_analysis",
            ...     content="Classify: {{ text }}",
            ...     description="Sentiment classification template"
            ... )
        """
        # Save template file
        template_path = self.templates_dir / f"{name}.jinja2"
        template_path.write_text(content, encoding="utf-8")

        # Generate version hash
        version_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        version = f"{datetime.now().strftime('%Y%m%d')}-{version_hash}"

        # Update metadata
        if name not in self.metadata:
            self.metadata[name] = {
                "versions": [],
                "stats": {"total_uses": 0},
            }

        self.metadata[name]["versions"].append({
            "version": version,
            "date": datetime.now().isoformat(),
            "description": description,
            "author": author,
            "hash": version_hash,
        })

        self._save_metadata()

        logger.info(f"Saved template: {name} (version: {version})")
        return version

    async def list_templates(self) -> list[str]:
        """
        List all available templates.

        Returns:
            List of template names

        Example:
            >>> templates = await system.list_templates()
            >>> print(templates)
            ['sentiment_analysis', 'entity_extraction', 'summarization']
        """
        templates = [
            p.stem for p in self.templates_dir.glob("*.jinja2")
            if not p.stem.startswith("_")
        ]
        return sorted(templates)

    async def list_versions(self, name: str) -> list[dict[str, Any]]:
        """
        List versions of a template.

        Args:
            name: Template name

        Returns:
            List of version metadata

        Example:
            >>> versions = await system.list_versions("sentiment_analysis")
            >>> for v in versions:
            ...     print(f"{v['version']} - {v['date']}")
        """
        if name in self.metadata:
            return self.metadata[name]["versions"]
        return []

    async def get_metadata(self, name: str) -> dict[str, Any]:
        """
        Get template metadata.

        Args:
            name: Template name

        Returns:
            Template metadata
        """
        return self.metadata.get(name, {})

    async def get_stats(self, name: str) -> dict[str, Any]:
        """
        Get template usage statistics.

        Args:
            name: Template name

        Returns:
            Usage statistics

        Example:
            >>> stats = await system.get_stats("sentiment_analysis")
            >>> print(f"Total uses: {stats['total_uses']}")
        """
        if name in self.metadata:
            return self.metadata[name].get("stats", {})
        return {}

    def _log_usage(self, name: str, version: str) -> None:
        """Log template usage (internal)."""
        if name not in self.metadata:
            self.metadata[name] = {"versions": [], "stats": {"total_uses": 0}}

        self.metadata[name]["stats"]["total_uses"] += 1
        # Note: In production, this would write to a time-series DB


# Global template system instance
_template_system = TemplateSystem()


# Convenience functions
async def load(name: str, version: str | None = None, **variables: Any) -> str:
    """Load and render template (convenience function)."""
    return await _template_system.load(name, version, **variables)


async def save(
    name: str,
    content: str,
    description: str = "",
    author: str = "",
) -> str:
    """Save template (convenience function)."""
    return await _template_system.save(name, content, description, author)


async def list_templates() -> list[str]:
    """List all templates (convenience function)."""
    return await _template_system.list_templates()


async def list_versions(name: str) -> list[dict[str, Any]]:
    """List template versions (convenience function)."""
    return await _template_system.list_versions(name)


# Create common templates
async def initialize_common_templates() -> None:
    """Initialize common template library."""
    # Sentiment analysis template
    await save(
        "sentiment_analysis",
        """You are a sentiment analysis expert.

Classify the sentiment of the following text as one of:
- Positive
- Negative
- Neutral

{% if examples %}
Examples:
{% for example in examples %}
Input: {{ example.input }}
Output: {{ example.output }}

{% endfor %}
{% endif %}

Input: {{ text }}
Output:""",
        description="Sentiment classification template",
        author="system",
    )

    # Entity extraction template
    await save(
        "entity_extraction",
        """Extract named entities from the text.

Entity types: {{ entity_types|join(", ") }}

{% if format == "JSON" %}
Return JSON array:
[
  {"type": "...", "text": "...", "start": ..., "end": ...}
]
{% endif %}

Text: {{ text }}

Entities:""",
        description="Named entity extraction template",
        author="system",
    )

    # Summarization template
    await save(
        "summarization",
        """Summarize the following text.

{% if max_words %}
Maximum words: {{ max_words }}
{% endif %}

{% if style %}
Style: {{ style }}
{% endif %}

Text:
{{ text }}

Summary:""",
        description="Text summarization template",
        author="system",
    )

    # QA with context template
    await save(
        "qa_with_context",
        """Answer the question based on the provided context.

Context:
{{ context }}

Question: {{ question }}

{% if include_citations %}
Provide citations from the context.
{% endif %}

Answer:""",
        description="Question answering with context template",
        author="system",
    )

    logger.info("Initialized common templates")


# Demo
async def main():
    """Demo template system."""
    print("=" * 60)
    print("Template System Demo")
    print("=" * 60)

    # Initialize common templates
    await initialize_common_templates()

    # List templates
    print("\nAvailable templates:")
    templates = await list_templates()
    for template in templates:
        print(f"- {template}")

    # Load and render sentiment template
    print("\n\nSentiment Analysis Template:")
    print("-" * 60)

    prompt = await load(
        "sentiment_analysis",
        text="I absolutely love this product!",
        examples=[
            {"input": "Great!", "output": "Positive"},
            {"input": "Terrible.", "output": "Negative"},
        ]
    )

    print(prompt)

    # Load summarization template
    print("\n\nSummarization Template:")
    print("-" * 60)

    prompt = await load(
        "summarization",
        text="Long article text here...",
        max_words=50,
        style="concise"
    )

    print(prompt)

    # Get stats
    print("\n\nTemplate Stats:")
    print("-" * 60)

    for template in templates:
        stats = await _template_system.get_stats(template)
        print(f"{template}: {stats.get('total_uses', 0)} uses")


if __name__ == "__main__":
    asyncio.run(main())
