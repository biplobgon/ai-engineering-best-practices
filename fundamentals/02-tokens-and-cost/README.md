# 02: Tokens & Cost - LLM Pricing Economics

**Time:** 45-60 minutes

---

## Why Cost Matters

LLM costs can spiral quickly:

```
1M requests × 1K tokens/request × $3/1M tokens = $3,000/day
→ $90,000/month

With caching (90% hit rate):
100K new requests × 1K tokens × $3/1M = $300/day
→ $9,000/month (10× savings)
```

**Key insight:** Small optimizations compound at scale.

---

## LLM Pricing Models

### 1. Per-Token Pricing (Most Common)

**Formula:** `Cost = (input_tokens × input_price) + (output_tokens × output_price)`

**Why separate pricing?**
- **Input:** Cheaper (just encoding/attention)
- **Output:** Expensive (generation is compute-intensive)

### 2. Tiered Pricing

Some providers offer volume discounts:

| Tier | Volume | Price |
|---|---|---|
| Free | 0-100K tokens | $0 |
| Standard | 100K-10M | $3/1M |
| Enterprise | 10M+ | $2/1M |

### 3. Cached vs Uncached

**Prompt caching** (Anthropic, OpenAI):
- First call: Full price
- Cached prefix: 90% discount
- Only changed suffix charged

---

## Model Pricing Comparison (June 2026)

| Model | Input ($/1M) | Output ($/1M) | Context | Speed |
|---|---|---|---|---|
| GPT-4o | $5.00 | $15.00 | 128K | Medium |
| GPT-4o-mini | $0.15 | $0.60 | 128K | Fast |
| Claude 3.5 Sonnet | $3.00 | $15.00 | 200K | Medium |
| Claude 3.5 Haiku | $0.80 | $4.00 | 200K | Fast |
| Gemini 1.5 Pro | $3.50 | $10.50 | 2M | Slow |
| Gemini 1.5 Flash | $0.35 | $1.05 | 1M | Fast |
| Llama 3.3 70B (Groq) | $0.59 | $0.79 | 128K | Very Fast |

**Notes:**
- Prices change frequently - always check official docs
- Embeddings: ~$0.02-0.13 per 1M tokens
- Fine-tuning: 10-100× training cost

---

## Cost Calculation Examples

### Example 1: Simple Chat

```python
Input: "Summarize this article: [5000 tokens]"
Output: 200 tokens
Model: GPT-4o-mini

Cost = (5000 × $0.15/1M) + (200 × $0.60/1M)
     = $0.00075 + $0.00012
     = $0.00087 (~$0.001)
```

### Example 2: RAG Pipeline

```python
1. Embedding 100 docs (50K tokens): $0.02 × 50/1000 = $0.001
2. Vector search: Free (local)
3. LLM call (1K input + 500 output): $0.0003 + $0.0003 = $0.0006

Total: ~$0.0016 per query
At 10K queries/day: $16/day = $480/month
```

### Example 3: Batch Processing

```python
Process 1M documents:
- 1M × 2K tokens avg = 2B tokens
- GPT-4o-mini input: 2B × $0.15/1M = $300
- Output (500 tokens avg): 500M × $0.60/1M = $300

Total: $600 (batch job)

With prompt caching (80% reuse):
- Uncached: 400M × $0.15/1M = $60
- Cached: 1.6B × $0.015/1M = $24
Total: $84 + $300 output = $384 (36% savings)
```

---

## Cost Optimization Strategies

### 1. Model Selection

**Trade-off:** Quality vs Cost vs Latency

```
High quality needed (analysis): Claude 3.5 Sonnet
Medium quality (chat): GPT-4o-mini
Low quality (classification): Haiku
```

**LLM Router Pattern:**
```python
if task.complexity == "simple":
    model = "gpt-4o-mini"  # $0.0001/call
elif task.complexity == "medium":
    model = "claude-haiku"  # $0.0005/call
else:
    model = "gpt-4o"  # $0.005/call
```

### 2. Prompt Compression

**Before (150 tokens):**
```
Please analyze the following text and provide a detailed 
summary including key points, themes, and recommendations:
[text]
```

**After (50 tokens):**
```
Summarize key points and recommendations:
[text]
```

**Savings:** 67% fewer input tokens

### 3. Output Token Limits

```python
# Unbounded (risky)
response = llm.chat(messages)  # Could generate 4K tokens

# Bounded (safe)
response = llm.chat(messages, max_tokens=200)  # Max $0.0001
```

### 4. Caching

**Exact cache:** Same prompt → cached response (free)

**Semantic cache:** Similar prompt → cached response if similarity > 0.93

**Prompt caching:** Reuse long context prefix (90% discount)

---

## Cost Monitoring & Budgets

### Per-Request Budget

```python
MAX_COST_PER_REQUEST = 0.01  # $0.01

estimated_cost = calculate_cost(tokens_in, tokens_out, model)
if estimated_cost > MAX_COST_PER_REQUEST:
    raise BudgetExceededError()
```

### Daily Budget

```python
DAILY_BUDGET = 100.0  # $100/day

current_spend = get_daily_spend()
if current_spend + estimated_cost > DAILY_BUDGET:
    # Use cheaper model or reject request
    model = "gpt-4o-mini"
```

### Cost Tracking

Track metrics:
- **Total cost:** Sum of all LLM calls
- **Cost per user:** Identify expensive users
- **Cost per endpoint:** Optimize high-cost routes
- **Cache hit rate:** Measure caching effectiveness

---

## Model Quality vs Cost Tradeoffs

| Use Case | Recommended Model | Cost/Request | Quality |
|---|---|---|---|
| Classification | GPT-4o-mini, Haiku | $0.0001 | 85% |
| Chatbot | GPT-4o-mini | $0.0005 | 90% |
| Code generation | GPT-4o, Sonnet | $0.002 | 95% |
| Complex analysis | GPT-4o, Sonnet | $0.005 | 98% |
| Embedding | text-embedding-3-small | $0.00001 | N/A |

**Rule of thumb:** Start with cheapest model that meets quality bar.

---

## Hands-On Exercises

See `cost_calculator.py` for:
1. Calculate cost for any model/token combination
2. Compare costs across models
3. Estimate monthly costs from usage patterns
4. Calculate ROI for caching

See `model_comparison.py` for:
1. Compare models by price, speed, quality
2. Find cheapest model for quality threshold
3. Simulate cost with different strategies
4. Visualize cost/quality tradeoffs

---

## Interview Questions

**Q: How is LLM pricing calculated?**  
A: `(input_tokens × input_price) + (output_tokens × output_price)`. Output is typically 3-10× more expensive than input.

**Q: What's the difference between GPT-4o and GPT-4o-mini?**  
A: GPT-4o-mini is 30× cheaper but slightly lower quality. Good for simple tasks.

**Q: How can you reduce LLM costs by 10×?**  
A: Caching (90% hit rate), prompt compression, output limits, cheaper models for simple tasks, batch processing.

**Q: What is prompt caching?**  
A: Caching long context prefixes (e.g., system prompt, docs) at 90% discount. Only changed suffix is charged.

**Q: How much does embedding cost vs LLM calls?**  
A: Embeddings are ~100× cheaper ($0.02/1M tokens vs $2-5/1M tokens for LLMs).

---

## Key Takeaways

✅ **Output tokens cost 3-10× more:** Limit max_tokens  
✅ **Caching saves 90%+:** Implement exact + semantic caching  
✅ **Model selection matters:** Use cheapest model that meets quality bar  
✅ **Prompt compression:** Shorter prompts = lower cost  
✅ **Monitor spending:** Track cost per request, user, endpoint  
✅ **Budget enforcement:** Hard limits prevent runaway costs

---

## Next Lesson

[03: Sampling Parameters](../03-sampling-params/) - Learn how temperature, top_p, and other parameters control LLM behavior.
