"""
Batching for throughput optimization.

Exports:
- batch_chat: Parallel LLM calls
- batch_embed: Batch embeddings
- CoalescingCache: Dedupe in-flight requests
- ConcurrentBatcher, AdaptiveBatcher: Advanced batching
"""

from cost_optimization.batching.concurrent_calls import (
    ConcurrentBatcher,
    AdaptiveBatcher,
    batch_chat,
    batch_process,
)
from cost_optimization.batching.embed_batching import (
    batch_embed,
    batch_embed_with_retry,
    EmbeddingBatcher,
    estimate_embedding_cost,
)
from cost_optimization.batching.request_coalescing import (
    CoalescingCache,
    coalesced_call,
)


__all__ = [
    "ConcurrentBatcher",
    "AdaptiveBatcher",
    "batch_chat",
    "batch_process",
    "batch_embed",
    "batch_embed_with_retry",
    "EmbeddingBatcher",
    "estimate_embedding_cost",
    "CoalescingCache",
    "coalesced_call",
]
