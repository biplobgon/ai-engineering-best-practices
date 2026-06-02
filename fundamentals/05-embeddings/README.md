# 05: Embeddings - Semantic Search & Similarity

**Time:** 45-60 minutes

---

## What Are Embeddings?

**Embedding:** A dense vector representation of text that captures semantic meaning.

```
Text: "The cat sat on the mat"
Embedding: [0.23, -0.45, 0.12, ..., 0.78]  (1536 dimensions)

Similar text: "A feline rested on the rug"
Embedding: [0.24, -0.44, 0.13, ..., 0.76]  (very close!)
```

**Key insight:** Semantically similar texts have similar embeddings (close in vector space).

---

## Why Embeddings Matter

### Traditional keyword search (fails):
```
Query: "machine learning"
Document: "AI and neural networks"
Match: ❌ No shared keywords
```

### Semantic search with embeddings (works):
```
Query embedding: [0.5, 0.3, ...]
Doc embedding:   [0.52, 0.31, ...]
Similarity: 0.95 ✅ High match!
```

**Applications:**
- Semantic search
- Recommendation systems
- Clustering & classification
- Duplicate detection
- Semantic caching

---

## Embedding Models

| Model | Dimensions | Cost/1M tokens | Use Case |
|---|---|---|---|
| text-embedding-3-small | 1536 | $0.02 | General purpose, fast |
| text-embedding-3-large | 3072 | $0.13 | Higher quality |
| text-embedding-ada-002 | 1536 | $0.10 | Legacy (OpenAI) |
| Voyage-2 | 1024 | $0.12 | Specialized retrieval |
| Cohere Embed v3 | 1024 | $0.10 | Multilingual |

**Rule of thumb:** Start with `text-embedding-3-small` (best value).

---

## How Embeddings Work

### 1. Text → Vector
```python
text = "Machine learning is a subset of AI"
embedding = embed(text)
# → [0.23, -0.45, 0.12, ..., 0.78]  (1536 numbers)
```

### 2. Compare Vectors with Cosine Similarity
```python
similarity = cosine_similarity(vec1, vec2)
# → 0.95 (range: -1 to 1, higher = more similar)
```

### 3. Find Similar Items
```
Query: "How to learn Python?"

Docs:
1. "Python tutorials" → similarity: 0.92 ✅
2. "JavaScript guide" → similarity: 0.45
3. "Python course" → similarity: 0.89 ✅
```

---

## Cosine Similarity

**Formula:** Measures angle between vectors (not distance).

```
cos(θ) = (A · B) / (||A|| × ||B||)

Range: -1 to 1
- 1.0: Identical
- 0.8-0.9: Very similar
- 0.5-0.7: Somewhat similar
- <0.5: Not similar
```

**Why cosine (not Euclidean distance)?**
- Cosine measures direction (semantic meaning)
- Euclidean measures magnitude (less meaningful for embeddings)

---

## Embedding Best Practices

### 1. Use Same Model for Query & Documents
```python
# ❌ Bad: Different models
query_emb = embed(query, model="text-embedding-3-small")
doc_emb = embed(doc, model="text-embedding-3-large")
similarity(query_emb, doc_emb)  # ❌ Incomparable

# ✅ Good: Same model
query_emb = embed(query, model="text-embedding-3-small")
doc_emb = embed(doc, model="text-embedding-3-small")
similarity(query_emb, doc_emb)  # ✅ Comparable
```

### 2. Batch Embeddings for Efficiency
```python
# ❌ Slow: One at a time
for text in texts:
    emb = embed([text])  # 100 API calls

# ✅ Fast: Batch
embeddings = embed(texts)  # 1 API call
```

### 3. Cache Embeddings
```
Embedding cost: $0.02 per 1M tokens
If you re-embed same text 100 times: $2 wasted

Solution: Cache embeddings in database
```

### 4. Normalize Text Before Embedding
```python
# ❌ Bad: Inconsistent
"Hello World!" → embed()
"hello world" → embed()  # Different embeddings!

# ✅ Good: Normalize
normalize("Hello World!") → "hello world" → embed()
```

---

## Storage & Retrieval

### Store Embeddings in Vector Database

**Options:**
- **Pinecone:** Managed, scalable
- **Weaviate:** Open-source, feature-rich
- **Chroma:** Lightweight, local
- **pgvector:** PostgreSQL extension
- **FAISS:** Facebook's similarity search (local)

**Schema:**
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    text TEXT,
    embedding VECTOR(1536),  -- pgvector
    metadata JSONB
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

### Query Similar Documents
```sql
SELECT id, text, 1 - (embedding <=> query_embedding) AS similarity
FROM documents
WHERE 1 - (embedding <=> query_embedding) > 0.7
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

---

## Semantic Search Pipeline

```
1. Index Phase (one-time):
   - Split documents into chunks
   - Generate embeddings for each chunk
   - Store in vector database

2. Query Phase (real-time):
   - User query → embed()
   - Search vector DB for similar chunks
   - Return top-k results
   - (Optional) Pass to LLM for final answer
```

---

## Chunking Strategies

**Problem:** Documents are too long to embed in one go.

**Solution:** Split into chunks.

| Strategy | Chunk Size | Overlap | Use Case |
|---|---|---|---|
| Fixed-size | 500 tokens | 50 tokens | General purpose |
| Sentence-based | ~5 sentences | 1 sentence | Preserve meaning |
| Paragraph-based | 1 paragraph | None | Natural boundaries |
| Semantic | Variable | Dynamic | Advanced (clustering) |

**Best practice:** 300-500 tokens per chunk with 10% overlap.

---

## Embedding Limitations

### 1. Token Limit
```
text-embedding-3-small: 8192 tokens max
Longer text → truncate or chunk
```

### 2. Language/Domain Specificity
```
General model: "Python course" ↔ "Programming tutorial" = 0.85
Code-specific model: Same comparison = 0.92 (better)
```

### 3. Cold Start Problem
```
No existing documents → No embeddings → No search results
Solution: Start with seed documents
```

### 4. Computational Cost
```
Embedding 1M docs (500 tokens each) = 500M tokens
Cost: 500M × $0.02/1M = $10

Vector DB storage: ~6KB per doc (1536 dims × 4 bytes)
1M docs = 6GB storage
```

---

## Advanced: Hybrid Search

Combine keyword search + semantic search for best results.

```python
# Keyword search (fast, exact matches)
keyword_results = search_keywords(query)

# Semantic search (slow, semantic matches)
semantic_results = search_embeddings(query)

# Combine with weights
final_results = merge(
    keyword_results * 0.3,
    semantic_results * 0.7
)
```

**Result:** Best of both worlds.

---

## Hands-On Exercises

See `embedding_demo.py` for:
1. Create embeddings using core/llm
2. Calculate cosine similarity
3. Find similar documents
4. Visualize embeddings in 2D (PCA/t-SNE)

See `similarity_search.py` for:
1. Build a simple semantic search engine
2. Index documents with embeddings
3. Query and retrieve similar documents
4. Compare with keyword search

---

## Interview Questions

**Q: What is an embedding?**  
A: A dense vector representation of text that captures semantic meaning. Similar texts have similar embeddings.

**Q: What is cosine similarity?**  
A: A metric measuring the cosine of the angle between two vectors. Range: -1 to 1. Higher = more similar.

**Q: When should you use embeddings vs keyword search?**  
A: Embeddings for semantic similarity, keyword search for exact matches. Best: hybrid approach.

**Q: How do you handle documents longer than embedding model's token limit?**  
A: Chunk documents into smaller pieces (300-500 tokens), embed each chunk separately.

**Q: What's the difference between text-embedding-3-small and text-embedding-3-large?**  
A: Small: 1536 dims, $0.02/1M, faster. Large: 3072 dims, $0.13/1M, higher quality. Small is usually sufficient.

**Q: How do you store embeddings at scale?**  
A: Use vector databases (Pinecone, Weaviate, pgvector) with indexing (HNSW, IVF) for fast retrieval.

---

## Key Takeaways

✅ **Embeddings = semantic meaning as vectors**  
✅ **Cosine similarity measures semantic similarity**  
✅ **Use same model for query & documents**  
✅ **Batch embeddings for efficiency**  
✅ **Cache embeddings (don't re-compute)**  
✅ **Chunk long documents (300-500 tokens)**  
✅ **Store in vector database for fast search**  
✅ **Hybrid search (keyword + semantic) is best**

---

## Next Steps

**You've completed the Fundamentals!**

Next modules:
- [Prompt Engineering](../../prompt-engineering/) - Craft effective prompts
- [RAG Systems](../../rag/) - Build production-grade retrieval systems
- [Testing](../../testing/) - Test LLM applications
- [Production Deployment](../../deployment/) - Deploy to production

**Congratulations!** You now understand the core fundamentals of LLM engineering.
