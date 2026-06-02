"""
Latency optimization module.

Provides streaming, parallel execution, and async patterns
to reduce response time and improve user experience.
"""

from latency_optimization.parallel_tool_calls.concurrent_tools import (
    parallel_execute,
    parallel_map,
    parallel_with_timeout,
)
from latency_optimization.parallel_tool_calls.parallel_embeddings import (
    batch_embed,
    adaptive_batch_embed,
)


__all__ = [
    # Parallel execution
    "parallel_execute",
    "parallel_map",
    "parallel_with_timeout",
    
    # Parallel embeddings
    "batch_embed",
    "adaptive_batch_embed",
]
