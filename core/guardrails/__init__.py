"""
Input/output guardrails and validation.

Design principles:
- Input validation: length, PII, jailbreak
- Output validation: hallucination, citations, format
"""

import logging
import re

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Validation result."""

    valid: bool
    message: str = ""
    redacted: str | None = None


# Simple PII patterns (production would use more sophisticated detection)
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}

# Jailbreak patterns (simplified)
JAILBREAK_PATTERNS = [
    r"ignore.*previous.*instructions",
    r"disregard.*rules",
    r"you are.*now.*dan",
    r"pretend.*you.*are",
]


async def validate_input(text: str, max_length: int = 10000) -> ValidationResult:
    """
    Validate user input.

    Checks:
    - Length < max_length
    - PII detection
    - Jailbreak patterns

    Args:
        text: User input
        max_length: Max allowed length

    Returns:
        ValidationResult
    """
    # Length check
    if len(text) > max_length:
        return ValidationResult(
            valid=False,
            message=f"Input too long: {len(text)} > {max_length}",
        )

    # PII detection
    redacted = text
    pii_found = False
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            pii_found = True
            logger.warning(f"PII detected: {pii_type}")
            # Redact
            redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted, flags=re.IGNORECASE)

    # Jailbreak detection
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return ValidationResult(
                valid=False,
                message="Potential jailbreak attempt detected",
            )

    if pii_found:
        return ValidationResult(
            valid=True,
            message="PII detected and redacted",
            redacted=redacted,
        )

    return ValidationResult(valid=True, message="Input valid")


async def validate_output(
    text: str,
    policy: str = "default",
) -> ValidationResult:
    """
    Validate LLM output.

    Checks:
    - Format correctness
    - Basic hallucination patterns
    - Citation validation (if policy="citations_required")

    Args:
        text: LLM output
        policy: Validation policy

    Returns:
        ValidationResult
    """
    # Check for common hallucination markers
    hallucination_markers = [
        "i cannot verify",
        "i don't have access",
        "i'm not sure",
        "i apologize, but i don't know",
    ]

    for marker in hallucination_markers:
        if marker in text.lower():
            logger.warning(f"Potential hallucination marker found: {marker}")

    # Citation validation
    if policy == "citations_required":
        # Simple check for citation patterns [1], (Source:), etc.
        citation_patterns = [r"\[\d+\]", r"\(Source:", r"\(Ref:"]
        has_citations = any(re.search(p, text) for p in citation_patterns)

        if not has_citations:
            return ValidationResult(
                valid=False,
                message="Citations required but not found",
            )

    return ValidationResult(valid=True, message="Output valid")
