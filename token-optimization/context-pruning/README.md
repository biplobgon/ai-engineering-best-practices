# Context Pruning

**Focus:** Filter documents by relevance to reduce token usage in RAG systems.

---

## Overview

Context pruning is critical for RAG systems where you retrieve 20+ documents but can only fit 3-5 in the prompt.

Two main techniques:

1. **Relevance Filtering** - Score by query similarity, keep top-k
2. **Embedding-based Pruning** - Semantic deduplication and clustering

---

## Relevance Filtering

### What it does
Scores each document by similarity to query, keeps top-k most relevant.

### Performance
- **Reduction:** 60-80% (20 docs → 3-5 docs)
- **Latency:** 50-200ms (embedding + scoring)
- **Quality:** High (keeps best matches)

### Example

```python
from token_optimization.context_pruning.relevance_filtering import filter_by_similarity

query = "What are the best practices for prompt engineering?"
docs = retrieve_documents(query, top_k=20)  # 15,000 tokens

relevant = await filter_by_similarity(
    query=query,
    documents=docs,
    top_k=5,
)  # 3,500 tokens (77% reduction)
```

---

## Embedding-based Pruning

### What it does
Removes duplicate/similar documents using semantic clustering.

### Performance
- **Reduction:** 40-60%
- **Latency:** 100-300ms
- **Quality:** Medium (may remove useful variations)

### Example

```python
from token_optimization.context_pruning.embedding_based_pruning import deduplicate_by_embeddings

docs = retrieve_documents(query, top_k=20)

unique_docs = await deduplicate_by_embeddings(
    documents=docs,
    similarity_threshold=0.85,  # 85% similar = duplicate
)
```

---

## Usage Patterns

### Standard RAG pipeline
```python
# Step 1: Retrieve broadly
docs = retrieve_documents(query, top_k=20)

# Step 2: Filter by relevance
relevant = await filter_by_similarity(query, docs, top_k=10)

# Step 3: Deduplicate
unique = await deduplicate_by_embeddings(relevant, threshold=0.85)

# Step 4: Use top 5
final_docs = unique[:5]
```

### Hybrid scoring
```python
from token_optimization.context_pruning.relevance_filtering import hybrid_score

# Combine vector similarity + keyword match
scored_docs = await hybrid_score(
    query=query,
    documents=docs,
    vector_weight=0.7,
    keyword_weight=0.3,
)
```

---

## Files

- [`relevance_filtering.py`](./relevance_filtering.py) - Query-based filtering
- [`embedding_based_pruning.py`](./embedding_based_pruning.py) - Deduplication
- [`tests/`](./tests/) - Unit tests and benchmarks
