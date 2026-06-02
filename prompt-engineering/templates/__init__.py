"""
Prompt template system.

Available modules:
- template_system: Load and manage reusable templates
- meta_prompts: Prompts that generate prompts (planned)
- system_messages: Pre-built role definitions (planned)
"""

from prompt_engineering.templates import template_system


__all__ = [
    "template_system",
]
