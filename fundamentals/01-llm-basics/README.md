# 01: LLM Basics - Tokens & Tokenization

**Time:** 30-45 minutes

---

## What Are Tokens?

**Token:** The fundamental unit of text that an LLM processes. Not characters, not words—subword chunks.

### Why Subwords?

- **Vocabulary efficiency:** 50K-100K tokens covers most languages
- **Unknown word handling:** Can represent any word via subword pieces
- **Cost basis:** LLM pricing is per-token, not per-word

### Example Tokenization

```
Text: "Hello, world! 🌍"

Tokens (GPT-4):
["Hello", ",", " world", "!", " 🌍"]
→ 5 tokens

Tokens (Claude):
["Hello", ",", " world", "!", " ", "🌍"]
→ 6 tokens
```

**Key insight:** Different models tokenize differently. Always use the model's tokenizer.

---

## How Tokenization Works

### BPE (Byte-Pair Encoding)

Most models (GPT, Claude) use BPE or variants:

1. Start with character vocabulary
2. Find most frequent character pairs
3. Merge them into new token
4. Repeat until target vocabulary size

### Result

- Common words: 1 token (`"the"`, `"is"`, `"and"`)
- Uncommon words: Multiple tokens (`"superintelligent"` → `["super", "intell", "igent"]`)
- Code: Often more tokens (variable names, symbols)

---

## Token Counts by Content Type

| Content Type | Tokens per 1000 chars | Example |
|---|---|---|
| English prose | ~200-250 | "The quick brown fox..." |
| Code (Python) | ~300-400 | `def function(x): return x**2` |
| JSON | ~250-350 | `{"key": "value", "num": 123}` |
| Emoji-heavy text | ~400-500 | "Hello 👋 world 🌍" |

**Rule of thumb:** 1 token ≈ 4 characters in English, ≈ 0.75 words

---

## Why Tokens Matter

### 1. Cost
```
100K tokens @ $3/1M = $0.30
But if you counted wrong: 150K tokens @ $3/1M = $0.45
→ 50% cost overrun
```

### 2. Context Limits
```
Model: 128K context limit
Your doc: 130K tokens
→ Request fails (or truncates)
```

### 3. Latency
```
More tokens = slower generation
1K tokens @ 50 tokens/sec = 20 seconds
100 tokens @ 50 tokens/sec = 2 seconds
```

---

## Common Tokenizer Libraries

| Library | Models | Language |
|---|---|---|
| `tiktoken` | OpenAI (GPT-3.5, GPT-4) | Python |
| `transformers` | HuggingFace models | Python |
| `anthropic` | Claude (unofficial) | Python |
| LiteLLM | All (via `litellm.token_counter`) | Python |

---

## Example: Counting Tokens

```python
import tiktoken

# OpenAI tokenizer
enc = tiktoken.encoding_for_model("gpt-4")
text = "Hello, world! How are you today?"
tokens = enc.encode(text)

print(f"Text: {text}")
print(f"Tokens: {tokens}")
print(f"Count: {len(tokens)}")
# Output: Count: 8
```

---

## Tradeoffs: Characters vs Words vs Tokens

| Metric | Characters | Words | Tokens (✅ Correct) |
|---|---|---|---|
| **Accuracy** | ❌ Off by 4× | ❌ Off by 1.3× | ✅ Exact |
| **Ease** | ✅ Simple | ✅ Simple | ⚠️ Requires tokenizer |
| **Cost Estimate** | ❌ Unreliable | ❌ Unreliable | ✅ Accurate |
| **Context Checking** | ❌ Wrong | ❌ Wrong | ✅ Correct |

**Bottom line:** Always count tokens, not characters or words.

---

## Hands-On Exercises

See `tokenization_demo.py` for:
1. Tokenize text with different models
2. Compare token counts (GPT vs Claude vs Llama)
3. Estimate cost from token count
4. Visualize tokens (show token boundaries)

See `token_counting.py` for:
1. Count tokens before API call
2. Reject requests exceeding budget
3. Estimate latency from token count

---

## Interview Questions

**Q: What is a token?**  
A: A subword unit of text that an LLM processes. Not a word or character, but a chunk (e.g., "ing", "pre", "cat").

**Q: Why not just use words?**  
A: Words have unbounded vocabulary. Subwords let models handle rare/unknown words, multilingual text, and code.

**Q: How many tokens is "Hello, world!"?**  
A: Depends on tokenizer, but typically 4-5 tokens (`["Hello", ",", " world", "!"]` or similar).

**Q: Why do tokens matter for cost?**  
A: LLM pricing is per-token (e.g., $3/1M tokens). Counting wrong = budget errors.

---

## Key Takeaways

✅ **Tokens ≠ words:** 1 token ≈ 0.75 words in English  
✅ **Always use tokenizer:** `tiktoken`, `transformers`, or LiteLLM  
✅ **Cost = tokens × price:** Count accurately  
✅ **Different models, different tokenizers:** GPT vs Claude tokenize differently  
✅ **Context limits are in tokens:** Not characters

---

## Next Lesson

[02: Tokens & Cost](../02-tokens-and-cost/) - Learn how to calculate LLM costs and compare models.
