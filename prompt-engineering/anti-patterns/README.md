# Anti-Patterns: What NOT to Do

Common prompt engineering mistakes and how to fix them.

## Overview

Learning from bad examples is as important as learning from good ones. This module shows:
- Common prompt engineering mistakes
- Why they fail
- How to fix them
- Before/after comparisons

## Anti-Patterns

### 1. Vague Instructions ❌
**Problem**: Ambiguous, unclear requirements

**Bad:**
```
Tell me about the product.
```

**Good:**
```
Analyze this product review and classify sentiment as Positive, Negative, or Neutral.
Explain your reasoning in 1-2 sentences.

Review: [text]
```

**Impact**: 40% improvement in accuracy

---

### 2. Overloaded Prompts ❌
**Problem**: Too many tasks in one prompt

**Bad:**
```
Analyze sentiment, extract entities, summarize, and translate to Spanish.
```

**Good:**
```
# Split into separate calls:
1. Analyze sentiment
2. Extract entities (separate call)
3. Summarize (separate call)
4. Translate (separate call)
```

**Impact**: 60% faster, 25% more accurate per task

---

### 3. No Output Format Specified ❌
**Problem**: Unpredictable output structure

**Bad:**
```
Extract people and places from the text.
```

**Good:**
```
Extract people and places from the text.

Return JSON:
{
  "people": ["name1", "name2"],
  "places": ["place1", "place2"]
}
```

**Impact**: 90% reduction in parsing errors

---

### 4. Too Many Few-Shot Examples ❌
**Problem**: 10+ examples (diminishing returns)

**Bad:**
```
Example 1: ...
Example 2: ...
...
Example 15: ...
```

**Good:**
```
# Use 2-5 carefully selected examples
Example 1: [most common case]
Example 2: [edge case]
Example 3: [another edge case]
```

**Impact**: 3x cheaper, same quality

---

### 5. Assuming Context ❌
**Problem**: LLM doesn't have your context

**Bad:**
```
How did the launch go?
```

**Good:**
```
Context: Our product launched on Jan 15, 2024. Sales were $50K in week 1.

Question: Based on this data, how did the launch perform?
```

**Impact**: 70% improvement in relevance

---

### 6. No Temperature Control ❌
**Problem**: Wrong temperature for task

**Bad:**
```
# Using temperature=0.9 for classification
Classify sentiment: [text]
```

**Good:**
```
# Use temperature=0 for deterministic tasks
# Use temperature=0.7-1.0 for creative tasks
Classify sentiment: [text]  # temperature=0
Write a story: [prompt]     # temperature=0.8
```

**Impact**: 50% more consistent outputs

---

### 7. Ignoring Token Costs ❌
**Problem**: Inefficient prompting wastes money

**Bad:**
```
# 2000 token prompt for simple task
You are a highly skilled expert with 20 years of experience...
[long backstory]
...
Question: Is this positive or negative? "I love it"
```

**Good:**
```
# 50 token prompt
Classify sentiment as Positive or Negative.
Text: "I love it"
```

**Impact**: 40x cheaper

---

### 8. No Error Handling ❌
**Problem**: Prompts fail on edge cases

**Bad:**
```python
# No validation
result = await llm.chat(prompt)
answer = result.text.split(":")[1]  # May crash
```

**Good:**
```python
# Validate output
result = await llm.chat(prompt)
try:
    answer = result.text.split(":")[1].strip()
    validate_answer(answer)
except Exception as e:
    logger.error(f"Parse error: {e}")
    answer = "Unable to determine"
```

**Impact**: 95% reduction in crashes

---

### 9. Hard-Coded Prompts ❌
**Problem**: Prompts scattered in codebase

**Bad:**
```python
# Prompts everywhere
def sentiment(text):
    prompt = f"Classify: {text}"
    ...

def extract(text):
    prompt = f"Extract entities: {text}"
    ...
```

**Good:**
```python
# Use template system
from templates import load

async def sentiment(text):
    prompt = await load("sentiment_analysis", text=text)
    ...
```

**Impact**: 10x easier to maintain and version

---

### 10. No Evaluation ❌
**Problem**: Can't measure prompt quality

**Bad:**
```python
# Deploy without testing
prompt = "Classify sentiment: {text}"
# Hope it works...
```

**Good:**
```python
# Test on eval set
results = evaluate_prompt(
    prompt_template,
    eval_set=test_data,
    metric="accuracy"
)
print(f"Accuracy: {results['accuracy']:.2%}")
```

**Impact**: Catch regressions before deployment

---

## Cost Impact Summary

| Anti-Pattern | Token Waste | Cost Impact | Fix Complexity |
|--------------|-------------|-------------|----------------|
| Vague Instructions | +30% | +30% | Easy |
| Overloaded Prompts | +50% | +50% | Medium |
| No Format Spec | +20% | +20% | Easy |
| Too Many Examples | +300% | +300% | Easy |
| Assuming Context | +40% | +40% | Easy |
| Wrong Temperature | Varies | Varies | Easy |
| Token Inefficiency | +200% | +200% | Easy |
| No Error Handling | N/A | Varies | Medium |
| Hard-Coded Prompts | N/A | Maintenance | Medium |
| No Evaluation | N/A | Risk | Medium |

## Testing Your Prompts

### Checklist
- [ ] Instructions are clear and specific
- [ ] Output format is specified
- [ ] Using appropriate pattern (zero-shot vs few-shot)
- [ ] Temperature set correctly
- [ ] Token count is reasonable
- [ ] Error handling in place
- [ ] Tested on edge cases
- [ ] Measured on eval set
- [ ] Versioned in template system
- [ ] Cost per call documented

## Before/After Examples

See `examples.py` for 20+ before/after comparisons with metrics.

## Interview Questions

### Pattern Recognition
1. **Why avoid vague instructions?** LLMs need specificity; ambiguity leads to inconsistent outputs.
2. **What's wrong with 15 few-shot examples?** Diminishing returns after 3-5; wastes tokens and money.
3. **Why specify output format?** Reduces parsing errors by 90%, makes integration reliable.

### Design Questions  
4. **How to detect prompt anti-patterns in PR reviews?** Linting rules, token budgets, format validation, eval gates.
5. **Design a system to prevent anti-patterns.** Template system + eval framework + CI checks + cost alerts.
6. **How to refactor hard-coded prompts?** Extract to template system, version, A/B test, measure impact.

## References

- [OpenAI Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Engineering](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [Google's Prompt Engineering Guide](https://ai.google.dev/docs/prompt_best_practices)

---

*Learn from these mistakes to build better prompts.*
