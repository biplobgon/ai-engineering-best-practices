"""
Tests for template system.

Run with: pytest prompt-engineering/templates/tests/ -v
"""

import pytest

from prompt_engineering.templates import template_system


@pytest.mark.asyncio
class TestTemplateSystem:
    """Test template system."""

    async def test_save_and_load(self):
        """Test saving and loading templates."""
        # Save template
        version = await template_system.save(
            "test_template",
            "Hello {{ name }}!",
            description="Test template"
        )

        assert version is not None
        assert len(version) > 0

        # Load template
        result = await template_system.load("test_template", name="World")

        assert "Hello World!" in result

    async def test_list_templates(self):
        """Test listing templates."""
        # Save a test template
        await template_system.save("test_list", "Test content")

        # List all templates
        templates = await template_system.list_templates()

        assert isinstance(templates, list)
        assert "test_list" in templates

    async def test_template_with_conditionals(self):
        """Test template with Jinja2 conditionals."""
        content = """{% if show_examples %}
Examples: {{ examples|join(", ") }}
{% endif %}
Query: {{ query }}"""

        await template_system.save("test_conditional", content)

        # With examples
        result = await template_system.load(
            "test_conditional",
            show_examples=True,
            examples=["A", "B"],
            query="Test"
        )

        assert "Examples: A, B" in result
        assert "Query: Test" in result

        # Without examples
        result = await template_system.load(
            "test_conditional",
            show_examples=False,
            query="Test"
        )

        assert "Examples:" not in result
        assert "Query: Test" in result

    async def test_metadata_tracking(self):
        """Test metadata tracking."""
        await template_system.save(
            "test_metadata",
            "Content",
            description="Test description",
            author="test_user"
        )

        metadata = await template_system.get_metadata("test_metadata")

        assert "versions" in metadata
        assert len(metadata["versions"]) > 0

        version_info = metadata["versions"][0]
        assert "description" in version_info
        assert version_info["description"] == "Test description"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
