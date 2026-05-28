"""
Input/output guardrails and validation.

Design principles:
- Input validation: length, PII, jailbreak
- Output validation: hallucination, citations, format
"""

from typing import Optional


class ValidationResult:
    """Validation result."""

    valid: bool
    """Whether validation passed."""

    message: str
    """Failure reason (if invalid)."""

    redacted: Optional[str] = None
    """Redacted text (if PII detected)."""


async def validate_input(text: str) -> ValidationResult:
    """
    Validate user input.

    Checks:
    - Length < context window
    - No excessive PII
    - No jailbreak patterns
    - Language detection (optional)

    Args:
        text: User input

    Returns:
        ValidationResult with valid, message, redacted text
    """
    raise NotImplementedError


async def validate_output(
    text: str,
    policy: str = "default",
) -> ValidationResult:
    """
    Validate LLM output.

    Checks:
    - Format correctness
    - Hallucination detection
    - Citation validation (if applicable)

    Args:
        text: LLM output
        policy: Validation policy (e.g., "default", "strict", "citations_required")

    Returns:
        ValidationResult
    """
    raise NotImplementedError
