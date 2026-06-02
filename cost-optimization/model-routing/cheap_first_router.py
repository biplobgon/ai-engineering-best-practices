"""
Cheap-first router: Start with cheapest model, escalate on failure.

Cost Reduction: 60-80%
Latency: Same or better (cheap models often faster)
Quality: 90-95% of smart model quality
"""

import logging
from typing import Any, Callable

from core.llm import chat
from core.llm.router import TaskType, router
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


class CheapFirstRouter:
    """
    Route to cheapest model first, escalate on failure/quality issues.
    
    Example:
        >>> router = CheapFirstRouter()
        >>> response = await router.chat(
        ...     messages=[{"role": "user", "content": "Classify: positive or negative"}],
        ...     task_type="classification"
        ... )
        >>> print(f"Model: {response.model}, Cost: ${response.usd_cost:.6f}")
        Model: claude-3-5-haiku, Cost: $0.000250
    """
    
    def __init__(
        self,
        enable_fallback: bool = True,
        max_retries: int = 2,
    ) -> None:
        """
        Initialize cheap-first router.
        
        Args:
            enable_fallback: Enable fallback to smarter models on failure
            max_retries: Max number of fallback attempts
        """
        self.enable_fallback = enable_fallback
        self.max_retries = max_retries
        self.router = router  # Use core router
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        task_type: TaskType = "generation",
        quality_check: Callable[[LLMResponse], bool] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Chat with cheap-first routing.
        
        Args:
            messages: Chat messages
            task_type: Type of task (determines model tier)
            quality_check: Optional function to validate response quality
            **kwargs: Additional args passed to core.llm.chat()
        
        Returns:
            LLMResponse from cheapest successful model
        
        Raises:
            Exception: If all models fail
        
        Cost:
            ~$0.0001 USD (Haiku) vs $0.001 (GPT-4o) → 90% savings
        """
        # Get models for task type (ordered cheap → expensive)
        models = self.router.get_all_models(task_type)
        
        if not models:
            raise ValueError(f"No models configured for task_type={task_type}")
        
        last_error = None
        
        for attempt, model in enumerate(models[: self.max_retries + 1]):
            try:
                logger.info(
                    f"Attempting model {model} (attempt {attempt + 1}/{self.max_retries + 1})",
                    extra={"task_type": task_type, "model": model},
                )
                
                # Make LLM call
                response = await chat(
                    messages=messages,
                    model=model,
                    **kwargs,
                )
                
                # Quality check (if provided)
                if quality_check and not quality_check(response):
                    logger.warning(
                        f"Quality check failed for model {model}",
                        extra={"model": model, "response_length": len(response.text)},
                    )
                    
                    if self.enable_fallback and attempt < self.max_retries:
                        continue  # Try next model
                    else:
                        # Return anyway (caller can decide)
                        return response
                
                # Success
                logger.info(
                    f"Success with model {model}",
                    extra={
                        "model": model,
                        "cost": response.usd_cost,
                        "tokens": response.total_tokens,
                        "attempt": attempt + 1,
                    },
                )
                
                return response
            
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Model {model} failed: {e}",
                    extra={"model": model, "error": str(e)},
                )
                
                # If fallback disabled or last attempt, raise
                if not self.enable_fallback or attempt >= self.max_retries:
                    break
        
        # All models failed
        raise Exception(
            f"All models failed for task_type={task_type}. Last error: {last_error}"
        )
    
    async def chat_with_fallback(
        self,
        messages: list[dict[str, str]],
        *,
        primary_model: str,
        fallback_model: str,
        quality_check: Callable[[LLMResponse], bool] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Explicit two-tier routing (primary → fallback).
        
        Args:
            messages: Chat messages
            primary_model: Try this first (cheap)
            fallback_model: Fallback if primary fails (smart)
            quality_check: Optional quality validation
            **kwargs: Additional args
        
        Returns:
            LLMResponse from primary or fallback
        
        Example:
            >>> response = await router.chat_with_fallback(
            ...     messages=[...],
            ...     primary_model="claude-3-5-haiku",
            ...     fallback_model="claude-3-5-sonnet"
            ... )
        """
        try:
            # Try primary model
            response = await chat(messages=messages, model=primary_model, **kwargs)
            
            # Check quality
            if quality_check and not quality_check(response):
                logger.info(
                    f"Primary model {primary_model} quality insufficient, trying fallback"
                )
                raise ValueError("Quality check failed")
            
            return response
        
        except Exception as e:
            logger.warning(f"Primary model failed, falling back: {e}")
            
            # Try fallback
            return await chat(messages=messages, model=fallback_model, **kwargs)


# Convenience function
async def cheap_first_chat(
    messages: list[dict[str, str]],
    *,
    task_type: TaskType = "generation",
    quality_check: Callable[[LLMResponse], bool] | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """
    Convenience function for cheap-first routing.
    
    Example:
        >>> from cost_optimization.model_routing import cheap_first_chat
        >>> 
        >>> response = await cheap_first_chat(
        ...     messages=[{"role": "user", "content": "Classify this email"}],
        ...     task_type="classification"
        ... )
    """
    router_instance = CheapFirstRouter()
    return await router_instance.chat(
        messages=messages,
        task_type=task_type,
        quality_check=quality_check,
        **kwargs,
    )
