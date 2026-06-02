"""
Prompt engineering patterns.

Available patterns:
- zero_shot: Simple instruction, no examples
- few_shot: 2-5 examples before query
- chain_of_thought: Step-by-step reasoning
- react_pattern: Reasoning + acting with tools
- self_consistency: Multiple paths, majority vote
"""

from prompt_engineering.patterns import (
    chain_of_thought,
    few_shot,
    react_pattern,
    self_consistency,
    zero_shot,
)


__all__ = [
    "zero_shot",
    "few_shot",
    "chain_of_thought",
    "react_pattern",
    "self_consistency",
]
