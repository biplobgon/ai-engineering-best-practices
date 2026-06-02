# Summarization Pipelines

**Focus:** Multi-stage summarization strategies for different use cases.

---

## Overview

Three main approaches:

1. **Extractive** - Select key sentences (fast, exact quotes)
2. **Abstractive** - LLM-powered paraphrasing (slow, compact)
3. **Hierarchical** - Map-reduce pattern (best for long documents)

---

## Extractive Summarization

### What it does
Selects most important sentences using scoring algorithms.

### Performance
- **Reduction:** 70-85%
- **Latency:** 100-300ms (no LLM calls)
- **Quality:** Medium-High (preserves exact wording)

### When to use
✅ Legal/compliance documents
✅ When exact quotes needed
✅ Fast summarization required
❌ Narrative content (extractive can be choppy)

---

## Abstractive Summarization

### What it does
Uses LLM to paraphrase and compress content.

### Performance
- **Reduction:** 80-90%
- **Latency:** 2-5s per pass
- **Quality:** High (reads naturally)

### When to use
✅ Long documents
✅ Narrative content
✅ Quality over speed
❌ Time-sensitive applications
❌ Cost-sensitive applications

---

## Hierarchical Summarization

### What it does
Map-reduce pattern: chunk → summarize → combine → repeat.

### Performance
- **Reduction:** 90-95%
- **Latency:** 10-30s for 100+ page docs
- **Quality:** Medium-High

### When to use
✅ Very long documents (50+ pages)
✅ Multi-document synthesis
✅ Research reports
❌ Short documents
❌ Real-time applications

---

## Files

- [`extractive_summary.py`](./extractive_summary.py) - Sentence selection
- [`abstractive_summary.py`](./abstractive_summary.py) - LLM-powered
- [`hierarchical_summary.py`](./hierarchical_summary.py) - Map-reduce
- [`tests/`](./tests/) - Unit tests and benchmarks
