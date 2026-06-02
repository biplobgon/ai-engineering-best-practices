# Fundamentals

**Status:** ✅ Phase 3

Master the absolute foundations of LLM engineering: tokens, sampling, context, embeddings, and cost mechanics.

---

## What You'll Learn

1. **Tokens & Tokenization** - How text becomes numbers, subword splitting, vocabulary
2. **Cost Mechanics** - Token pricing, cost calculation, model selection economics
3. **Sampling Parameters** - Temperature, top_p, max_tokens, stop sequences, frequency_penalty
4. **Context Windows** - Context limits, sliding windows, strategies for long documents
5. **Embeddings** - Dense vectors, similarity search, embedding models, chunking strategies

---

## Module Structure

```
fundamentals/
├── 01-llm-basics/
│   ├── README.md               # Token fundamentals
│   ├── tokenization_demo.py    # Hands-on tokenization
│   ├── token_counting.py       # Count tokens for cost estimation
│   └── tests/
├── 02-tokens-and-cost/
│   ├── README.md               # Pricing mechanics
│   ├── cost_calculator.py      # Calculate LLM costs
│   ├── model_comparison.py     # Compare models by cost/quality
│   └── tests/
├── 03-sampling-params/
│   ├── README.md               # Sampling explained
│   ├── temperature_demo.py     # Explore temperature effects
│   ├── sampling_strategies.py  # Different parameter combos
│   └── tests/
├── 04-context-windows/
│   ├── README.md               # Context management
│   ├── sliding_window.py       # Handle long documents
│   ├── context_pruning.py      # Keep only relevant context
│   └── tests/
└── 05-embeddings/
    ├── README.md               # Vector fundamentals
    ├── embedding_demo.py       # Create and compare embeddings
    ├── similarity_search.py    # Semantic search basics
    └── tests/
```

---

## Learning Path

**Time:** 1 week (2-3 hours per lesson)

**Prerequisites:** 
- Python 3.12+
- Basic async/await understanding
- Core SDK installed (Phase 2)

**Order:**
1. Start with 01-llm-basics (understand tokens)
2. Then 02-tokens-and-cost (understand economics)
3. Then 03-sampling-params (control output)
4. Then 04-context-windows (manage scale)
5. Finally 05-embeddings (semantic search)

---

## Key Takeaways

| Concept | Key Insight | Rule of Thumb |
|---|---|---|
| **Tokens** | ~4 chars/token in English | 1000 words ≈ 750 tokens |
| **Cost** | Input tokens cheaper than output | Haiku: $0.80/1M tokens |
| **Temperature** | 0 = deterministic, 1 = creative | 0.7 for most tasks |
| **Context** | Models have hard limits | GPT-4: 128K, Claude: 200K |
| **Embeddings** | Fixed-size vectors (1536d) | Cosine similarity for search |

---

## Anti-Patterns to Avoid

❌ **Counting characters instead of tokens** - Always use tiktoken or model's tokenizer  
❌ **Ignoring output token costs** - Output often 3-5× more expensive than input  
❌ **Using temperature=1 for factual tasks** - High temp = hallucinations  
❌ **Sending entire documents as context** - Chunk and retrieve relevant pieces  
❌ **Re-embedding unchanged text** - Cache embeddings aggressively

---

## Cost Optimization Quick Wins

1. **Use cheap models for simple tasks** - Haiku for classification, Sonnet for reasoning
2. **Count tokens before API calls** - Estimate cost, reject over-budget requests
3. **Cache embeddings** - Embedding same text twice is waste
4. **Prune context** - Remove irrelevant context before sending
5. **Use prompt caching** - Anthropic/OpenAI cache repeated context

---

## Interview Questions

**Junior:**
- What is a token? How does tokenization work?
- How do you calculate the cost of an LLM call?
- What does temperature do?

**Mid:**
- How would you handle a 100K token document with a 32K context model?
- When would you use temperature=0 vs temperature=0.7 vs temperature=1?
- What's the difference between embeddings and LLM text generation?

**Senior:**
- Design a cost-optimized system for 1M+ queries/day
- How would you implement semantic caching using embeddings?
- What are the tradeoffs between different embedding models?

---

## Next Steps

After completing fundamentals:
- → [Prompt Engineering](../prompt-engineering/) to learn patterns
- → [Cost Optimization](../cost-optimization/) for advanced techniques
- → [RAG](../rag/) to build retrieval systems
