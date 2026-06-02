"""
Multi-tier fallback strategy with retry logic and quality checks.

Handles:
- API errors (rate limits, timeouts)
- Quality failures (empty response, validation errors)
- Confidence thresholds
"""

import logging
from enum import Enum
from typing import Any, Callable

from core.llm import chat
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Model tiers by capability and cost."""
    
    CHEAP = "cheap"  # Haiku, GPT-4o-mini
    SMART = "smart"  # Sonnet, GPT-4o
    PREMIUM = "premium"  # Opus (if needed)


class FallbackRouter:
    """
    Multi-tier fallback with retry and quality validation.
    
    Architecture:
        Tier 1 (Cheap):  Try cheap model first
        Tier 2 (Smart):  Fallback on failure/quality issues
        Tier 3 (Premium): Last resort (optional)
    
    Example:
        >>> router = FallbackRouter()
        >>> response = await router.chat_with_tiers(
        ...     messages=[{"role": "user", "content": "Complex reasoning task"}],
        ...     min_quality_score=0.8
        ... )
    """
    
    def __init__(self) -> None:
        """Initialize fallback router with tier mappings."""
        self._tier_models: dict[ModelTier, list[str]] = {
            ModelTier.CHEAP: [
                "anthropic/claude-3-5-haiku-20241022",
                "openai/gpt-4o-mini",
            ],
            ModelTier.SMART: [
                "anthropic/claude-3-5-sonnet-20241022",
                "openai/gpt-4o",
            ],
            ModelTier.PREMIUM: [
                "anthropic/claude-3-opus-20240229",  # If available
            ],
        }
    
    def _get_model_for_tier(self, tier: ModelTier) -> str:
        """Get first available model in tier."""
        models = self._tier_models.get(tier, [])
        if not models:
            raise ValueError(f"No models configured for tier {tier}")
        return models[0]
    
    async def chat_with_tiers(
        self,
        messages: list[dict[str, str]],
        *,
        start_tier: ModelTier = ModelTier.CHEAP,
        quality_check: Callable[[LLMResponse], bool] | None = None,
        min_quality_score: float | None = None,
        max_tier: ModelTier = ModelTier.SMART,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Chat with tier-based fallback.
        
        Args:
            messages: Chat messages
            start_tier: Initial tier to try (default: CHEAP)
            quality_check: Custom quality validation function
            min_quality_score: Minimum quality score (0-1)
            max_tier: Maximum tier to try (default: SMART)
            **kwargs: Additional args for chat()
        
        Returns:
            LLMResponse from first successful tier
        
        Raises:
            Exception: If all tiers fail
        
        Example:
            >>> # Start cheap, escalate to smart if needed
            >>> response = await router.chat_with_tiers(
            ...     messages=[{"role": "user", "content": "Classify sentiment"}],
            ...     start_tier=ModelTier.CHEAP,
            ...     min_quality_score=0.8
            ... )
        """
        # Define tier order
        tiers = [ModelTier.CHEAP, ModelTier.SMART, ModelTier.PREMIUM]
        start_idx = tiers.index(start_tier)
        max_idx = tiers.index(max_tier)
        
        active_tiers = tiers[start_idx : max_idx + 1]
        
        last_error = None
        last_response = None
        
        for tier in active_tiers:
            try:
                model = self._get_model_for_tier(tier)
                
                logger.info(
                    f"Trying tier {tier.value} with model {model}",
                    extra={"tier": tier.value, "model": model},
                )
                
                # Make LLM call
                response = await chat(messages=messages, model=model, **kwargs)
                
                # Quality checks
                if quality_check and not quality_check(response):
                    logger.warning(
                        f"Quality check failed for tier {tier.value}",
                        extra={"tier": tier.value, "model": model},
                    )
                    last_response = response
                    continue  # Try next tier
                
                if min_quality_score and hasattr(response, "quality_score"):
                    if response.quality_score < min_quality_score:
                        logger.warning(
                            f"Quality score {response.quality_score:.2f} below threshold",
                            extra={
                                "tier": tier.value,
                                "score": response.quality_score,
                                "threshold": min_quality_score,
                            },
                        )
                        last_response = response
                        continue  # Try next tier
                
                # Success
                logger.info(
                    f"Success with tier {tier.value}",
                    extra={
                        "tier": tier.value,
                        "model": model,
                        "cost": response.usd_cost,
                    },
                )
                
                return response
            
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Tier {tier.value} failed: {e}",
                    extra={"tier": tier.value, "error": str(e)},
                )
                continue
        
        # All tiers failed
        if last_response:
            # Return last response (even if low quality)
            logger.warning("All tiers failed quality checks, returning last response")
            return last_response
        
        raise Exception(f"All tiers failed. Last error: {last_error}")
    
    async def chat_with_confidence_fallback(
        self,
        messages: list[dict[str, str]],
        *,
        min_confidence: float = 0.8,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Fallback based on model confidence score.
        
        Args:
            messages: Chat messages
            min_confidence: Minimum confidence threshold (0-1)
            **kwargs: Additional args
        
        Returns:
            LLMResponse with confidence ≥ threshold
        
        Example:
            >>> response = await router.chat_with_confidence_fallback(
            ...     messages=[{"role": "user", "content": "Uncertain classification"}],
            ...     min_confidence=0.85
            ... )
        
        Note:
            Assumes model returns confidence in structured output or via parsing.
        """
        def confidence_check(response: LLMResponse) -> bool:
            """Check if response has sufficient confidence."""
            # Try to extract confidence from response
            if hasattr(response, "confidence"):
                return response.confidence >= min_confidence
            
            # Try parsing from text (model might output "Confidence: 0.92")
            if "confidence" in response.text.lower():
                try:
                    # Simple regex extraction (improve as needed)
                    import re
                    match = re.search(r"confidence[:\s]+([0-9.]+)", response.text.lower())
                    if match:
                        confidence = float(match.group(1))
                        return confidence >= min_confidence
                except Exception:
                    pass
            
            # No confidence found → assume pass
            return True
        
        return await self.chat_with_tiers(
            messages=messages,
            quality_check=confidence_check,
            **kwargs,
        )


class FallbackReason(str, Enum):
    """Reasons for fallback escalation."""
    
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    QUALITY_FAILURE = "quality_failure"
    VALIDATION_ERROR = "validation_error"
    LOW_CONFIDENCE = "low_confidence"


def default_quality_check(response: LLMResponse) -> bool:
    """
    Default quality check for responses.
    
    Checks:
    - Non-empty response
    - Minimum length (>10 chars)
    - No error indicators in text
    
    Args:
        response: LLM response to validate
    
    Returns:
        True if quality acceptable, False otherwise
    """
    # Empty response
    if not response.text or len(response.text.strip()) == 0:
        logger.debug("Quality check failed: empty response")
        return False
    
    # Too short (likely error or refusal)
    if len(response.text.strip()) < 10:
        logger.debug("Quality check failed: response too short")
        return False
    
    # Error indicators
    error_phrases = [
        "i cannot",
        "i'm unable",
        "i don't have",
        "i apologize",
        "error:",
        "invalid",
    ]
    
    text_lower = response.text.lower()
    for phrase in error_phrases:
        if phrase in text_lower:
            logger.debug(f"Quality check failed: error phrase detected: {phrase}")
            return False
    
    return True


# Convenience function
async def fallback_chat(
    messages: list[dict[str, str]],
    *,
    quality_check: Callable[[LLMResponse], bool] | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """
    Convenience function for fallback routing.
    
    Example:
        >>> from cost_optimization.model_routing import fallback_chat
        >>> 
        >>> response = await fallback_chat(
        ...     messages=[{"role": "user", "content": "Complex task"}],
        ...     min_quality_score=0.8
        ... )
    """
    router = FallbackRouter()
    
    # Use default quality check if none provided
    if quality_check is None:
        quality_check = default_quality_check
    
    return await router.chat_with_tiers(
        messages=messages,
        quality_check=quality_check,
        **kwargs,
    )
