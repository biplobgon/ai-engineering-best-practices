"""
Model router for cost optimization (cheap-first routing).

Routes requests to cheapest appropriate model with fallback escalation.
"""

import logging
from typing import Literal

from core.config import get_settings


logger = logging.getLogger(__name__)

TaskType = Literal[
    "classification",
    "extraction",
    "generation",
    "reasoning",
    "summarization",
    "translation",
    "code",
    "fallback",
]


class Router:
    """Model router for cost optimization (cheap-first)."""

    def __init__(self) -> None:
        """Initialize router with model mappings."""
        self.settings = get_settings()

        # Model routing table (cheapest → most capable)
        self._routing_table: dict[TaskType, list[str]] = {
            "classification": [
                "anthropic/claude-3-5-haiku-20241022",
                "openai/gpt-4o-mini",
            ],
            "extraction": [
                "anthropic/claude-3-5-haiku-20241022",
                "openai/gpt-4o-mini",
            ],
            "generation": [
                "anthropic/claude-3-5-haiku-20241022",
                "openai/gpt-4o-mini",
                "anthropic/claude-3-5-sonnet-20241022",
            ],
            "reasoning": [
                "anthropic/claude-3-5-sonnet-20241022",
                "openai/gpt-4o",
            ],
            "summarization": [
                "anthropic/claude-3-5-haiku-20241022",
                "openai/gpt-4o-mini",
            ],
            "translation": [
                "anthropic/claude-3-5-haiku-20241022",
                "openai/gpt-4o-mini",
            ],
            "code": [
                "anthropic/claude-3-5-sonnet-20241022",
                "openai/gpt-4o",
            ],
            "fallback": [
                self.settings.FALLBACK_LLM,
            ],
        }

    def choose(self, task_type: TaskType = "generation") -> str:
        """
        Choose best model for task (defaults to cheapest in tier).

        Args:
            task_type: Type of task ("classification", "reasoning", etc.)

        Returns:
            Model name (e.g., "anthropic/claude-3-5-haiku-20241022")

        Example:
            >>> router.choose("classification")  # Returns cheapest model
            "anthropic/claude-3-5-haiku-20241022"
            >>> router.choose("reasoning")  # Returns smarter model
            "anthropic/claude-3-5-sonnet-20241022"
        """
        models = self._routing_table.get(task_type, [self.settings.DEFAULT_LLM])

        # Return first (cheapest) model in tier
        chosen = models[0] if models else self.settings.DEFAULT_LLM

        logger.debug(f"Router chose {chosen} for task_type={task_type}")
        return chosen

    def get_fallback(self, task_type: TaskType, current_model: str) -> str | None:
        """
        Get next fallback model if current fails.

        Args:
            task_type: Task type
            current_model: Model that failed

        Returns:
            Next model to try, or None if no fallback available

        Example:
            >>> router.get_fallback("generation", "anthropic/claude-3-5-haiku-20241022")
            "openai/gpt-4o-mini"
        """
        models = self._routing_table.get(task_type, [])

        try:
            current_idx = models.index(current_model)
            if current_idx + 1 < len(models):
                fallback = models[current_idx + 1]
                logger.info(
                    f"Falling back from {current_model} to {fallback}",
                    extra={"task_type": task_type},
                )
                return fallback
        except ValueError:
            pass

        return None

    def get_all_models(self, task_type: TaskType) -> list[str]:
        """Get all models for a task type (ordered by cost)."""
        return self._routing_table.get(task_type, [self.settings.DEFAULT_LLM])


# Global router instance
router = Router()
