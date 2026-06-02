# Token Optimization

**Status:** ✅ Phase 3 (Complete)

Reduce token usage through compression, context pruning, and summarization pipelines.

---

## What You'll Learn

- **Compression techniques** to reduce prompt size by 40-70%
- **Context pruning** using relevance filtering and embeddings
- **Summarization pipelines** (extractive, abstractive, hierarchical)
- **Token accounting** and cost tracking patterns
- **Production patterns** for memory-constrained applications

---

## Module Overview

| Aspect | Details |
|---|---|
| **Focus** | Token reduction, cost optimization, context management |
| **Complexity** | Intermediate |
| **Phase** | P3 |
| **Time** | 2-3 hours |

---

## Why Token Optimization Matters

### Cost Impact

```python
# Before optimization
prompt = load_entire_knowledge_base()  # 50,000 tokens
response = await chat([{"role": "user", "content": prompt}])
# Cost: ~$0.40 per request (Claude Sonnet)

# After optimization
compressed = prune_and_summarize(prompt)  # 5,000 tokens
response = await chat([{"role": "user", "content": compressed}])
# Cost: ~$0.04 per request (10x cheaper)
```

### Real-world scenarios:
- **RAG systems**: 20+ retrieved docs → 3-5 most relevant
- **Long conversations**: Sliding window + summarization
- **Document processing**: Hierarchical summarization for 100+ page docs
- **Multi-agent systems**: Compress shared context

---

## Key Techniques

### 1. Compression (40-60% reduction)

**Token pruning:**
- Remove filler words (`"um"`, `"like"`, `"you know"`)
- Strip markdown/HTML when not needed
- Collapse whitespace

**Recursive summarization:**
- Summarize in chunks
- Re-summarize summaries
- Preserve key facts

See: [`compression/`](./compression/)

---

### 2. Context Pruning (60-80% reduction)

**Relevance filtering:**
- Score documents by query similarity
- Keep top-k most relevant
- Use threshold cutoff

**Embedding-based pruning:**
- Semantic deduplication
- Cluster and sample
- MMR (Maximal Marginal Relevance)

See: [`context-pruning/`](./context-pruning/)

---

### 3. Summarization Pipelines (70-90% reduction)

**Extractive summarization:**
- Select key sentences
- Fast, preserves exact wording
- Good for facts/quotes

**Abstractive summarization:**
- LLM-powered paraphrasing
- More compact, more readable
- Higher cost

**Hierarchical (Map-Reduce):**
- Split into chunks
- Summarize each chunk
- Combine summaries
- Repeat until target size

See: [`summarization-pipelines/`](./summarization-pipelines/)

---

## Quick Start

### Install dependencies

```bash
pip install tiktoken scikit-learn numpy
```

### Example: Compress RAG context

```python
from token_optimization.context_pruning import relevance_filtering
from token_optimization.compression import token_pruning

# You have 20 retrieved docs
docs = retrieve_documents(query, top_k=20)  # ~15,000 tokens

# Step 1: Filter to most relevant
relevant_docs = await relevance_filtering.filter_by_similarity(
    query=query,
    documents=docs,
    top_k=5,  # Keep top 5
)  # ~4,000 tokens

# Step 2: Prune filler words
compressed = token_pruning.prune_tokens(relevant_docs)  # ~2,500 tokens

# Step 3: Use in prompt
prompt = f"Context:\n{compressed}\n\nQuestion: {query}"
response = await chat([{"role": "user", "content": prompt}])
```

**Result:** 15K → 2.5K tokens (83% reduction), cost savings of ~6x

---

## Directory Structure

```
token-optimization/
├── README.md                       # This file
├── compression/
│   ├── README.md                   # Compression techniques
│   ├── summarization_pipelines.py  # Recursive summarization
│   ├── token_pruning.py            # Remove filler words
│   └── tests/
│       ├── test_summarization.py
│       └── test_token_pruning.py
├── context-pruning/
│   ├── README.md                   # Relevance filtering
│   ├── relevance_filtering.py      # Top-k by similarity
│   ├── embedding_based_pruning.py  # Semantic deduplication
│   └── tests/
│       ├── test_relevance.py
│       └── test_embedding_pruning.py
└── summarization-pipelines/
    ├── README.md                   # Pipeline patterns
    ├── extractive_summary.py       # Sentence selection
    ├── abstractive_summary.py      # LLM-powered
    ├── hierarchical_summary.py     # Map-reduce
    └── tests/
        ├── test_extractive.py
        ├── test_abstractive.py
        └── test_hierarchical.py
```

---

## Performance Benchmarks

See individual modules for detailed benchmarks. Typical results:

| Technique | Token Reduction | Latency Overhead | Quality Loss |
|---|---|---|---|
| Token pruning | 15-30% | <1ms | Minimal |
| Relevance filtering | 60-80% | 50-200ms | Low (keeps best) |
| Extractive summary | 70-85% | 100-300ms | Medium |
| Abstractive summary | 80-90% | 2-5s | Low-Medium |
| Hierarchical summary | 90-95% | 10-30s | Medium |

**Rule of thumb:** Start with relevance filtering + token pruning (fast, high ROI).

---

## When to Use Each Technique

### Token Pruning
✅ Always use as first pass
✅ Chat transcripts
✅ User-generated content
❌ Code (may break syntax)
❌ Structured data (JSON)

### Relevance Filtering
✅ RAG systems (20+ docs)
✅ Knowledge base queries
✅ Long context windows
❌ When all context is critical

### Extractive Summarization
✅ Legal/compliance docs
✅ When exact quotes needed
✅ Fact-heavy content
❌ Narrative content

### Abstractive Summarization
✅ Long documents
✅ Narrative content
✅ When paraphrasing is OK
❌ Time-sensitive (slow)
❌ Cost-sensitive (uses LLM)

### Hierarchical Summarization
✅ 50+ page documents
✅ Multi-document synthesis
✅ Research reports
❌ Short documents
❌ Real-time applications

---

## Production Patterns

### 1. Hybrid Approach

```python
async def optimize_context(query: str, docs: list[str]) -> str:
    """Combines multiple techniques for max reduction."""
    
    # Step 1: Relevance filtering (80% reduction)
    relevant = await filter_by_similarity(query, docs, top_k=5)
    
    # Step 2: Token pruning (20% additional)
    pruned = prune_tokens(relevant)
    
    # Step 3: If still too long, summarize
    if count_tokens(pruned) > 4000:
        pruned = await extractive_summary(pruned, max_tokens=4000)
    
    return pruned
```

### 2. Caching Summaries

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_summary(doc_hash: str) -> str:
    """Cache expensive summarization."""
    return summarize(doc_hash)
```

### 3. Adaptive Compression

```python
async def adaptive_compress(text: str, max_tokens: int) -> str:
    """Automatically choose compression level."""
    current = count_tokens(text)
    
    if current <= max_tokens:
        return text
    elif current <= max_tokens * 1.5:
        return prune_tokens(text)
    elif current <= max_tokens * 3:
        return await extractive_summary(text, max_tokens)
    else:
        return await hierarchical_summary(text, max_tokens)
```

---

## Cost Analysis

### Scenario: RAG system (1M requests/month)

**Before optimization:**
- Average: 12,000 tokens/request
- Model: Claude Sonnet ($3/1M input tokens)
- Monthly cost: **$36,000**

**After optimization (80% reduction):**
- Average: 2,400 tokens/request
- Monthly cost: **$7,200**
- **Savings: $28,800/month ($345,600/year)**

**Optimization cost:**
- Embedding API: ~$200/month
- Compute overhead: ~$100/month
- **Net savings: $28,500/month**

---

## Common Pitfalls

### 1. Over-compression
❌ Removing critical context
✅ Always validate output quality

### 2. Ignoring latency
❌ Using abstractive summarization in real-time
✅ Pre-compute summaries offline

### 3. Not counting tokens
❌ Assuming character count = token count
✅ Use tiktoken for accurate counts

### 4. Forgetting instruction tokens
❌ Only compressing context
✅ Also optimize system prompts

---

## Next Steps

1. **Start here:** [`compression/token_pruning.py`](./compression/token_pruning.py)
2. **Then try:** [`context-pruning/relevance_filtering.py`](./context-pruning/relevance_filtering.py)
3. **Advanced:** [`summarization-pipelines/hierarchical_summary.py`](./summarization-pipelines/hierarchical_summary.py)

---

## Related Modules

- [`cost-optimization/`](../cost-optimization/) — Broader cost strategies
- [`latency-optimization/`](../latency-optimization/) — Speed techniques
- [`rag/`](../rag/) — Retrieval patterns
- [`core/llm/`](../core/llm/) — LLM client with token tracking

---

## References

- **Tiktoken:** Token counting library by OpenAI
- **LongLLMLingua:** Microsoft Research compression
- **RAPTOR:** Recursive summarization for RAG
- **Lost in the Middle:** Why context ordering matters

---

*Created in Phase 3. Updated: Jun 2026.*
