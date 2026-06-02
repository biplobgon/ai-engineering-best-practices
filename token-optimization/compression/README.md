# Compression Techniques

**Focus:** Reduce token count by removing noise and applying recursive summarization.

---

## Overview

This module provides two core compression techniques:

1. **Token Pruning** - Fast, rule-based removal of filler words
2. **Recursive Summarization** - LLM-powered multi-pass compression

---

## Token Pruning

### What it does
Removes filler words, excessive whitespace, and redundant punctuation.

### Performance
- **Reduction:** 15-30%
- **Latency:** <1ms
- **Quality loss:** Minimal

### Example

```python
from token_optimization.compression.token_pruning import prune_tokens

text = """
Um, well, you know, I think the main point is, like, 
we should definitely focus on the customer experience.
You know what I mean?
"""

compressed = prune_tokens(text)
# "I think the main point is we should focus on the customer experience."
```

---

## Recursive Summarization

### What it does
Summarizes text in multiple passes, progressively compressing until target size.

### Performance
- **Reduction:** 60-80% per pass
- **Latency:** 2-5s per pass
- **Quality loss:** Medium

### Example

```python
from token_optimization.compression.summarization_pipelines import recursive_summarize

doc = load_long_document()  # 10,000 tokens

compressed = await recursive_summarize(
    text=doc,
    target_tokens=1000,
    max_passes=3,
)
# 10,000 → 2,000 → 1,000 tokens (90% reduction)
```

---

## Usage Patterns

### Quick compression
```python
from token_optimization.compression import quick_compress

# Automatic method selection based on size
result = await quick_compress(text, target_tokens=500)
```

### Custom pipeline
```python
# Step 1: Prune (fast)
text = prune_tokens(original)

# Step 2: Check if more compression needed
if count_tokens(text) > target:
    text = await recursive_summarize(text, target_tokens=target)
```

---

## Files

- [`token_pruning.py`](./token_pruning.py) - Rule-based compression
- [`summarization_pipelines.py`](./summarization_pipelines.py) - LLM-based compression
- [`tests/`](./tests/) - Unit tests and benchmarks
