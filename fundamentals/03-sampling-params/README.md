# 03: Sampling Parameters - Control LLM Behavior

**Time:** 45-60 minutes

---

## What Are Sampling Parameters?

Sampling parameters control **how the LLM selects the next token** during generation.

**Key insight:** Same prompt + different parameters = vastly different outputs.

```python
# Deterministic (temperature=0)
"The capital of France is Paris."

# Creative (temperature=1.5)
"The capital of France? Well, some might say Paris, but there's 
also an argument for Versailles if we're talking about royal..."
```

---

## Core Sampling Parameters

### 1. Temperature

**What it does:** Controls randomness in token selection.

**Range:** 0.0 to 2.0 (typically 0.0 to 1.0)

**How it works:**
```
Low temperature (0.0):
- Token probabilities: [Paris: 99%, London: 0.5%, Berlin: 0.5%]
- Selection: Always "Paris" (deterministic)

High temperature (1.5):
- Token probabilities: [Paris: 40%, London: 30%, Berlin: 30%]
- Selection: Random (creative, diverse)
```

**Use cases:**

| Temperature | Use Case | Example |
|---|---|---|
| 0.0 | Extraction, classification | "Extract: {name, email, phone}" |
| 0.3 | Factual QA, summarization | "Summarize this article" |
| 0.7 | General chat, balanced | "Help me brainstorm ideas" |
| 1.0 | Creative writing, diversity | "Write a short story" |
| 1.5+ | Experimental, very creative | "Write surrealist poetry" |

**Rule of thumb:**
- **Deterministic tasks:** temperature = 0.0
- **Creative tasks:** temperature = 0.7-1.0
- **Default:** temperature = 0.7

---

### 2. Top-p (Nucleus Sampling)

**What it does:** Limits token selection to top cumulative probability.

**Range:** 0.0 to 1.0

**How it works:**
```
Token probabilities: [Paris: 60%, London: 25%, Berlin: 10%, Rome: 5%]

top_p = 0.9:
- Cumulative: Paris (60%) + London (25%) = 85% < 90%
- Add Berlin: 85% + 10% = 95% > 90% ✅
- Consider only: [Paris, London, Berlin]

top_p = 0.5:
- Cumulative: Paris (60%) > 50% ✅
- Consider only: [Paris]
```

**Use cases:**

| Top-p | Behavior | Use Case |
|---|---|---|
| 0.1 | Very focused | Classification, extraction |
| 0.5 | Moderately focused | Summarization |
| 0.9 | Balanced (default) | General chat |
| 1.0 | No filtering | Maximum creativity |

**Interaction with temperature:**
- Use **either** temperature **or** top_p, not both aggressively
- `temperature=0.7, top_p=0.9` is common balanced setting
- `temperature=0.0, top_p=1.0` is deterministic

---

### 3. Max Tokens

**What it does:** Limits maximum output length.

**Range:** 1 to model's max output (typically 4096-8192)

**Why it matters:**
```
Without max_tokens:
- Model might generate 4000 tokens
- Cost: 4000 tokens × $0.60/1M = $0.0024

With max_tokens=200:
- Model stops at 200 tokens
- Cost: 200 tokens × $0.60/1M = $0.00012
→ 20× cost reduction
```

**Use cases:**

| Max Tokens | Use Case |
|---|---|
| 10-50 | Classification, yes/no answers |
| 100-300 | Short summaries, chat responses |
| 500-1000 | Medium documents, explanations |
| 2000+ | Long-form content, reports |

**Best practice:** Always set `max_tokens` to prevent runaway generation.

---

### 4. Stop Sequences

**What it does:** Stop generation when specific string is encountered.

**Example:**
```python
stop=["</answer>", "\n\n"]

Output: "The answer is 42</answer> [STOP]"
# Stops before generating more text
```

**Use cases:**

| Stop Sequence | Use Case |
|---|---|
| `["\n"]` | Single-line responses |
| `["\n\n"]` | Paragraph breaks |
| `["</json>"]` | Structured output |
| `["User:", "Assistant:"]` | Chat formatting |

---

### 5. Frequency Penalty

**What it does:** Penalize tokens based on how often they've appeared.

**Range:** -2.0 to 2.0 (typically 0.0 to 1.0)

**How it works:**
```
frequency_penalty = 0.0:
- "The cat sat on the mat. The cat..."
- (Repetitive)

frequency_penalty = 1.0:
- "The cat sat on the mat. It purred..."
- (Avoids repeating "the cat")
```

**Use cases:**
- **0.0:** No penalty (default)
- **0.5:** Mild variety
- **1.0:** Strong variety (avoid repetition)

---

### 6. Presence Penalty

**What it does:** Penalize tokens that have appeared at all (regardless of frequency).

**Range:** -2.0 to 2.0 (typically 0.0 to 1.0)

**Difference from frequency penalty:**
```
Text: "cat cat cat dog"

frequency_penalty: Penalizes "cat" more (appeared 3×)
presence_penalty: Penalizes "cat" and "dog" equally (both appeared)
```

**Use cases:**
- **0.0:** No penalty (default)
- **0.5:** Encourage topic diversity
- **1.0:** Strong topic diversity

---

## Parameter Combinations for Common Tasks

### Classification
```python
{
    "temperature": 0.0,
    "max_tokens": 10,
    "top_p": 0.1,
}
# Deterministic, short, focused
```

### Summarization
```python
{
    "temperature": 0.3,
    "max_tokens": 300,
    "top_p": 0.9,
}
# Low creativity, controlled length
```

### General Chat
```python
{
    "temperature": 0.7,
    "max_tokens": 500,
    "top_p": 0.9,
    "frequency_penalty": 0.3,
}
# Balanced, avoid repetition
```

### Creative Writing
```python
{
    "temperature": 1.0,
    "max_tokens": 2000,
    "top_p": 0.95,
    "frequency_penalty": 0.5,
    "presence_penalty": 0.5,
}
# High creativity, diverse topics
```

### Code Generation
```python
{
    "temperature": 0.2,
    "max_tokens": 1000,
    "stop": ["```\n\n"],
}
# Low creativity (deterministic code), stop at code block end
```

---

## Advanced: How Sampling Works

### Step-by-step generation:

```
Input: "The capital of France is"

Step 1: Model predicts token probabilities
- Paris: 0.90
- London: 0.05
- Berlin: 0.03
- ...

Step 2: Apply temperature
- temperature=0.0 → Always pick "Paris"
- temperature=1.0 → Sample from [Paris: 90%, London: 5%, ...]

Step 3: Apply top_p
- top_p=0.95 → Consider [Paris, London, Berlin]
- top_p=0.50 → Consider [Paris only]

Step 4: Sample token
- Select "Paris"

Step 5: Repeat
- Input: "The capital of France is Paris"
- Predict next token: "."
```

---

## Common Pitfalls

### ❌ Pitfall 1: Using high temperature for factual tasks

```python
# Bad: High temperature for facts
response = llm.chat(
    messages=[{"role": "user", "content": "What is 2+2?"}],
    temperature=1.5,
)
# Output: "2+2 is approximately 4, or maybe 5..."
```

**Fix:** Use `temperature=0.0` for deterministic factual answers.

### ❌ Pitfall 2: No max_tokens limit

```python
# Bad: Unbounded output
response = llm.chat(messages)
# Output: 4000 tokens (expensive!)
```

**Fix:** Always set `max_tokens` based on use case.

### ❌ Pitfall 3: Combining aggressive temperature + top_p

```python
# Bad: Both high creativity controls
response = llm.chat(messages, temperature=1.5, top_p=0.5)
# Unpredictable behavior
```

**Fix:** Use temperature for creativity, top_p for safety/focus.

---

## Hands-On Exercises

See `temperature_demo.py` for:
1. Interactive temperature exploration (0.0 to 2.0)
2. Visualize how temperature affects output diversity
3. Compare same prompt at different temperatures
4. Find optimal temperature for different tasks

See `sampling_strategies.py` for:
1. Parameter combinations for common tasks
2. A/B test different sampling strategies
3. Measure output diversity with metrics
4. Build adaptive sampling (adjust based on task)

---

## Interview Questions

**Q: What is temperature in LLMs?**  
A: Controls randomness in token selection. 0.0 = deterministic, 1.0+ = creative.

**Q: When should you use temperature=0.0?**  
A: For deterministic tasks: classification, extraction, factual QA, code generation.

**Q: What's the difference between temperature and top_p?**  
A: Temperature adjusts probability distribution. Top_p limits tokens to top cumulative probability.

**Q: Why set max_tokens?**  
A: Prevent unbounded generation (cost control, latency, context limits).

**Q: What are stop sequences?**  
A: Strings that terminate generation early (e.g., `"\n\n"`, `"</json>"`).

---

## Key Takeaways

✅ **Temperature:** 0.0 = deterministic, 1.0 = creative  
✅ **Top_p:** Limits token selection to top cumulative probability  
✅ **Max_tokens:** Always set to prevent runaway generation  
✅ **Stop sequences:** Use for structured output  
✅ **Frequency/presence penalties:** Reduce repetition  
✅ **Match parameters to task:** Classification ≠ creative writing

---

## Next Lesson

[04: Context Windows](../04-context-windows/) - Learn how to manage long documents and context limits.
