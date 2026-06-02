# 04: Context Windows - Managing Long Documents

**Time:** 45-60 minutes

---

## What is a Context Window?

**Context window:** The maximum number of tokens (input + output) an LLM can process in a single call.

```
Context window: 128K tokens
Input: 120K tokens
Available for output: 8K tokens

If input > 128K → Request fails ❌
```

---

## Context Window Limits by Model

| Model | Context Window | Typical Use |
|---|---|---|
| GPT-4o | 128K tokens | ~96K words, ~300 pages |
| GPT-4o-mini | 128K tokens | ~96K words, ~300 pages |
| Claude 3.5 Sonnet | 200K tokens | ~150K words, ~460 pages |
| Claude 3.5 Haiku | 200K tokens | ~150K words, ~460 pages |
| Gemini 1.5 Pro | 2M tokens | ~1.5M words, ~4,600 pages |
| Gemini 1.5 Flash | 1M tokens | ~750K words, ~2,300 pages |

**Key insight:** Larger context ≠ always better. Considerations:
- **Cost:** More tokens = higher cost
- **Latency:** Longer context = slower processing
- **Quality:** LLMs can "lose focus" in very long contexts ("lost in the middle" problem)

---

## The "Lost in the Middle" Problem

LLMs perform worse on information buried in the middle of long contexts.

```
Performance by position in context:

Beginning: ████████████ 95% accuracy
Middle:    ██████░░░░░░ 60% accuracy  ← Lost in the middle
End:       ███████████░ 85% accuracy
```

**Solution:** Place critical information at the start or end of context.

---

## When You Exceed Context Limits

### Problem
```python
document = "..." # 150K tokens
model_context = 128K

# What happens?
response = llm.chat([{"role": "user", "content": document}])
# → Error: Context length exceeded
```

### Solutions

**1. Chunking + Map-Reduce**
```
Long doc → Split into chunks → Process each → Combine results

Doc (150K) → [Chunk1 (30K), Chunk2 (30K), ...] → 5 summaries → Final summary
```

**2. Sliding Window**
```
Process overlapping windows, maintain context

[───Window 1───]
      [───Window 2───]
            [───Window 3───]
```

**3. Compression/Pruning**
```
Keep only relevant parts, discard noise

Original: 150K tokens
Filtered: 50K tokens (critical content only)
```

**4. Use a larger context model**
```
GPT-4o (128K) → Gemini 1.5 Pro (2M)
```

---

## Context Management Strategies

### 1. Sliding Window

**Use case:** Processing long documents with continuity

**How it works:**
```python
window_size = 100_000  # tokens
overlap = 10_000       # tokens

Windows:
1. tokens[0:100_000]
2. tokens[90_000:190_000]  # 10K overlap
3. tokens[180_000:280_000]
```

**Pros:**
- Maintains context between chunks
- Good for summarization, analysis

**Cons:**
- Slower (multiple API calls)
- More expensive

---

### 2. Context Pruning

**Use case:** Extracting key information, dropping filler

**How it works:**
```python
# Original
"The meeting was held on Monday. John said hello. Mary discussed Q3 revenue..."

# Pruned (keep only revenue discussion)
"Mary discussed Q3 revenue..."
```

**Techniques:**
- **Keyword filtering:** Keep only sentences with important keywords
- **Embedding similarity:** Keep only sentences similar to query
- **Extractive summarization:** Keep most important sentences

**Pros:**
- Reduces cost
- Faster processing
- Focuses LLM on relevant content

**Cons:**
- Risk of losing important context
- Requires preprocessing

---

### 3. Hierarchical Summarization

**Use case:** Very long documents (100K+ tokens)

**How it works:**
```
Level 1: Split doc into 10 chunks → Summarize each (10 summaries)
Level 2: Combine 10 summaries → Summarize again (1 final summary)
```

**Example:**
```
Book (500K tokens)
→ 10 chapters × 50K tokens each
→ 10 chapter summaries × 2K tokens each = 20K total
→ 1 book summary × 2K tokens
```

**Pros:**
- Can handle unlimited length
- Parallelizable

**Cons:**
- Loses details
- Requires multiple API calls

---

### 4. Retrieval-Augmented Generation (RAG)

**Use case:** Q&A over large corpora

**How it works:**
```
1. User query: "What is the revenue?"
2. Retrieve relevant chunks from vector DB
3. Pass only relevant chunks to LLM
4. LLM answers based on retrieved context
```

**Pros:**
- Handles infinite corpus size
- Only processes relevant parts
- Cost-efficient

**Cons:**
- Requires embedding + vector DB
- Retrieval quality critical

---

## Token Counting for Context Management

**Always count tokens before making API calls:**

```python
import tiktoken

def fits_in_context(text: str, model: str = "gpt-4", max_output: int = 500) -> bool:
    enc = tiktoken.encoding_for_model(model)
    input_tokens = len(enc.encode(text))
    
    context_limit = 128_000  # GPT-4o
    total_needed = input_tokens + max_output
    
    return total_needed <= context_limit
```

---

## Cost vs Context Tradeoff

Larger context = higher cost, even if you don't use it all.

```
Short context (5K tokens):
- Cost: $0.0003 (Haiku)
- Latency: 0.5s

Long context (100K tokens):
- Cost: $0.008 (20× more)
- Latency: 3s (6× slower)
```

**Best practice:** Use only the context you need.

---

## Practical Patterns

### Pattern 1: Check Before Sending
```python
if count_tokens(document) > context_limit:
    # Use chunking or pruning
    chunks = split_into_chunks(document, chunk_size=50_000)
    results = [process_chunk(c) for c in chunks]
    final = combine_results(results)
else:
    # Direct processing
    final = llm.chat(document)
```

### Pattern 2: Adaptive Context
```python
def process_document(doc):
    tokens = count_tokens(doc)
    
    if tokens < 10_000:
        # Small: Process directly
        return process_small(doc)
    elif tokens < 100_000:
        # Medium: Use sliding window
        return process_medium(doc)
    else:
        # Large: Use hierarchical summarization
        return process_large(doc)
```

### Pattern 3: Smart Pruning
```python
def prune_to_budget(text: str, query: str, max_tokens: int = 100_000):
    # Embed all sentences
    sentences = split_sentences(text)
    embeddings = embed(sentences)
    
    # Embed query
    query_emb = embed([query])[0]
    
    # Rank by similarity
    similarities = cosine_similarity(query_emb, embeddings)
    ranked = sort_by_similarity(sentences, similarities)
    
    # Keep top sentences that fit budget
    pruned = keep_until_budget(ranked, max_tokens)
    
    return pruned
```

---

## Hands-On Exercises

See `sliding_window.py` for:
1. Split long documents into overlapping windows
2. Process each window with LLM
3. Combine results while maintaining coherence
4. Handle edge cases (boundaries, duplicates)

See `context_pruning.py` for:
1. Keyword-based filtering
2. Embedding-based similarity pruning
3. Extractive summarization
4. Cost comparison (original vs pruned)

---

## Interview Questions

**Q: What is a context window?**  
A: Maximum tokens (input + output) an LLM can process in one call. GPT-4o: 128K, Claude: 200K.

**Q: What happens if you exceed the context window?**  
A: Request fails with "context length exceeded" error.

**Q: What is the "lost in the middle" problem?**  
A: LLMs perform worse on information in the middle of long contexts. Place critical info at start/end.

**Q: How do you handle a 500K token document with a 128K context model?**  
A: Use chunking (map-reduce), sliding windows, pruning, hierarchical summarization, or switch to larger context model (Gemini 2M).

**Q: Why not always use the largest context window?**  
A: Cost (more tokens = higher cost), latency (longer = slower), quality (lost in the middle).

---

## Key Takeaways

✅ **Context window = input + output tokens**  
✅ **Different models have different limits (128K to 2M)**  
✅ **Always count tokens before API calls**  
✅ **Larger context ≠ better (cost, latency, quality)**  
✅ **"Lost in the middle" problem: Place key info at start/end**  
✅ **Strategies: Chunking, sliding window, pruning, RAG**  
✅ **Use only the context you need**

---

## Next Lesson

[05: Embeddings](../05-embeddings/) - Learn how to create and use embeddings for semantic search.
