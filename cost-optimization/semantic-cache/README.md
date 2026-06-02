**# Semantic Cache**

**Cost Reduction**: 40-60% | **Latency**: -95% (instant) | **Complexity**: Medium

## Concept

If user asks "How do I reset password?" and later "How to reset my password?", don't call LLM twice. Use semantic similarity (embeddings) to detect near-duplicates.

**Core Insight**: 40-60% of user queries are semantically similar to previous queries.

---

## Strategies

### 1. Exact Cache

Hash-based lookup (O(1), instant).

```python
key = hash(messages + model + params)
if key in cache:
    return cached_response  # $0 cost, 1ms latency
```

**Hit rate**: 10-20% (exact duplicates only)

---

### 2. Semantic Cache

Embedding-based similarity search.

```python
query_embedding = embed(query)
similar = find_similar(query_embedding, threshold=0.93)
if similar:
    return similar.response  # $0 cost, 50ms latency
```

**Hit rate**: 40-60% (near-duplicates)
**Cost**: Embed query ($0.00001) vs full LLM call ($0.001) → 99% savings

---

## Implementation

### Basic Semantic Cache

```python
from core.cache import semantic_cache
from core.llm import chat, embed

async def cached_chat(query: str):
    # Get embedding
    embedding = await embed([query])
    
    # Check semantic cache
    cached = await semantic_cache.get(query, embedding[0], threshold=0.93)
    if cached:
        return cached  # Cache hit
    
    # Cache miss → call LLM
    response = await chat([{"role": "user", "content": query}])
    
    # Store in cache
    await semantic_cache.set(query, embedding[0], response)
    
    return response
```

---

## Cost Analysis

### Real-World Workload (10K queries/day)

| Strategy | Cost/Day | Hit Rate | Avg Latency |
|---|---|---|---|
| No cache | $50 | 0% | 800ms |
| Exact cache | $40 | 20% | 400ms |
| Semantic cache (0.90) | $25 | 50% | 200ms |
| **Semantic cache (0.93)** | **$30** | **40%** | **300ms** |
| Semantic cache (0.95) | $35 | 30% | 400ms |

**Recommendation**: threshold=0.93 (balance hit rate + false positives)

---

## Threshold Tuning

| Threshold | Hit Rate | False Positives | Use Case |
|---|---|---|---|
| 0.85 | 70% | 15% | Low-stakes (FAQ bot) |
| 0.90 | 55% | 5% | General purpose |
| **0.93** | **40%** | **1%** | **Recommended** |
| 0.95 | 25% | 0.1% | High-stakes (medical) |
| 0.98 | 10% | 0% | Exact match only |

---

## Best Practices

### 1. Monitor Hit Rate

```python
hit_rate = cache_hits / (cache_hits + cache_misses)
# Target: 40-60% for most workloads
if hit_rate < 0.3:
    lower_threshold()  # More aggressive caching
elif hit_rate > 0.7:
    check_false_positives()  # Too aggressive?
```

### 2. Set TTL Based on Data Freshness

```python
# Static content (docs) → long TTL
await semantic_cache.set(query, emb, response, ttl=7*86400)  # 7 days

# Dynamic content (news) → short TTL
await semantic_cache.set(query, emb, response, ttl=3600)  # 1 hour
```

### 3. Invalidate on Content Changes

```python
# Document updated → clear related cache entries
await semantic_cache.clear_by_tag(f"doc:{doc_id}")
```

---

## Testing

```bash
pytest cost-optimization/semantic-cache/tests/
```

See also:
- [Model Routing](../model-routing/) — Stack caching + routing for 90% savings
- [Prompt Caching](../prompt-caching/) — Vendor-level prefix caching
