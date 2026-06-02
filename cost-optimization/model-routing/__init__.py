"""
Model routing for cost optimization.

Exports:
- CheapFirstRouter: Start cheap, escalate on failure
- FallbackRouter: Multi-tier fallback
- AdaptiveRouter: Learn from history
- Convenience functions: cheap_first_chat, fallback_chat, adaptive_chat
"""

from cost_optimization.model_routing.cheap_first_router import (
    CheapFirstRouter,
    cheap_first_chat,
)
from cost_optimization.model_routing.fallback_strategy import (
    FallbackRouter,
    ModelTier,
    default_quality_check,
    fallback_chat,
)
from cost_optimization.model_routing.adaptive_routing import (
    AdaptiveRouter,
    ModelStats,
    adaptive_chat,
)


__all__ = [
    "CheapFirstRouter",
    "cheap_first_chat",
    "FallbackRouter",
    "ModelTier",
    "default_quality_check",
    "fallback_chat",
    "AdaptiveRouter",
    "ModelStats",
    "adaptive_chat",
]
