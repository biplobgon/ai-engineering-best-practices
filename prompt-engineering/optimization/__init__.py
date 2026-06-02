"""
Prompt optimization techniques.

Available modules:
- token_reduction: Compress prompts by removing filler
- prompt_compression: Semantic compression
- auto_prompt_tuning: DSPy-style automatic optimization
"""

from prompt_engineering.optimization import token_reduction


__all__ = [
    "token_reduction",
]
