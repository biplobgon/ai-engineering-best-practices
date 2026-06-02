# Prompt Caching

**Cost Reduction**: 50-90% | **Latency**: -50% | **Complexity**: Low

## Concept

Vendors (Anthropic, OpenAI) cache prompt prefixes server-side. Reuse system messages / long context → 90% cheaper "read" tokens.

**Core Insight**: Most prompts have stable prefixes (system message, few-shot examples, long documents).

---

## Pricing (Anthropic Example)

| Token Type | Cost (Haiku) | Cost (Sonnet) |
|---|---|---|
| **Write** (first time) | $0.25 / 1M | $3.00 / 1M |
| **Read** (cached) | $0.03 / 1M | $0.30 / 1M |
| **Savings** | **88%** | **90%** |

---

## Implementation

### Anthropic Prefix Caching

```python
# System message gets cached (1024+ tokens)
system = "You are an expert..." * 500  # 2000 tokens

# First call: Write tokens
response1 = await chat(
    messages=[
        {"role": "user", "content": "Q1", "cache_control": {"type": "ephemeral"}}
    ],
    system=system,
    model="claude-3-5-sonnet"
)

# Subsequent calls: Read tokens (90% cheaper)
response2 = await chat(
    messages=[{"role": "user", "content": "Q2"}],
    system=system  # Cached prefix
)
```

---

## Cost Analysis

**Workload**: 10K requests with 5000-token system message

| Strategy | Write Cost | Read Cost | Total | Savings |
|---|---|---|---|---|
| No cache | $150 | $0 | $150 | 0% |
| **With cache** | **$15** | **$1.50** | **$16.50** | **89%** |

---

## Best Practices

### 1. Cache Stable Prefixes

```python
# ✅ Good: Stable system message
system = "You are helpful assistant. Always be polite..."

# ❌ Bad: Dynamic content in prefix
system = f"Today is {datetime.now()}"  # Changes every second
```

### 2. Minimum 1024 Tokens

```python
# Cache only works for 1024+ tokens
if len(system_tokens) < 1024:
    # Pad with few-shot examples or context
    system += few_shot_examples
```

---

## Testing

```bash
pytest cost-optimization/prompt-caching/tests/
```

See also:
- [Semantic Cache](../semantic-cache/) — Application-level caching
- [Model Routing](../model-routing/) — Combine for maximum savings
