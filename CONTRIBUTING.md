# Contributing to ai-engineering-best-practices

Welcome! This repository is built collectively. Here's how to contribute.

---

## Philosophy

1. **Production-grade first.** All code should be runnable, tested, logged, typed.
2. **Cost-conscious.** Every feature estimates token/cost impact.
3. **Modular.** Modules are independent; use `core/` for shared logic only.
4. **Documented.** Every module has a README.md with concept → examples → tradeoffs.
5. **Pedagogical.** Explain WHY, not just HOW.

---

## Getting Started

### Setup
```bash
git clone https://github.com/YOUR_GITHUB/ai-engineering-best-practices.git
cd ai-engineering-best-practices
make install
make up
make test
```

### Branch Naming
```
feature/module-name           # New module (e.g., feature/rag-reranker)
fix/issue-description         # Bug fix (e.g., fix/cache-ttl-logic)
docs/section                  # Documentation (e.g., docs/cost-handbook)
prompt/experiment             # Prompt experimentation (triggers eval-gate)
model/experiment              # Model routing experiment (triggers eval-gate)
```

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

Example:
```
feat(rag): add reranker support in hybrid retrieval

- Added Cohere reranker integration
- Updated retrieval benchmark to include ranking
- Cost: +$0.01 per query (at scale: $10K/1M queries)

Closes #42
```

---

## Code Standards

### Style & Linting
```bash
make fmt      # Black + Ruff
make lint     # Ruff + mypy
make test     # pytest
```

**Rules:**
- **Line length:** 100 chars
- **Python version:** 3.12+
- **Typing:** Required for public APIs; optional for internals
- **Docstrings:** Google-style for functions/classes
- **Logging:** Use structlog for all significant events

### Example: Writing a New Module Function

```python
"""core/llm/client.py"""

from typing import Optional
import structlog
from opentelemetry import trace

log = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


async def chat(
    messages: list[dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    cache: bool = True,
) -> dict[str, any]:
    """
    High-level chat interface with caching, retries, observability.
    
    Args:
        messages: List of {role, content} dicts
        model: Model name (defaults to DEFAULT_LLM)
        temperature: Sampling temperature [0, 2]
        max_tokens: Max output tokens
        cache: Check cache before calling LLM
    
    Returns:
        Response dict with 'text', 'tokens_in', 'tokens_out', 'usd_cost'
    
    Raises:
        ValueError: If messages format is invalid
        RateLimitError: If API rate limited (auto-retry with backoff)
    
    Cost:
        ~0.0001 USD per call (Haiku), less if cached.
    """
    with tracer.start_as_current_span("llm.chat") as span:
        span.set_attribute("model", model or DEFAULT_LLM)
        log.info("llm.chat", messages=len(messages), model=model, cache=cache)
        
        # Implementation...
        
        return response
```

---

## Testing

### Unit Tests
```bash
# Add test_my_feature.py in tests/
pytest tests/test_my_feature.py -v
```

**Pattern:**
```python
import pytest
from core.llm import chat

@pytest.mark.asyncio
async def test_chat_returns_valid_response():
    response = await chat([{"role": "user", "content": "Hi"}])
    assert "text" in response
    assert response["tokens_out"] > 0
    assert response["usd_cost"] >= 0

@pytest.mark.requires_api
async def test_chat_with_real_api():
    # Only runs if OPENAI_API_KEY is set
    response = await chat([{"role": "user", "content": "Say hello"}])
    assert len(response["text"]) > 0
```

### Integration Tests
- Use `@pytest.mark.integration`
- Mock external services (Redis, Postgres) when possible
- Real API tests: `@pytest.mark.requires_api`

### Eval Tests
- Use `@pytest.mark.eval`
- Compare output quality, cost, latency
- For prompt/model changes: required in PR

---

## Documentation

### Module README Template

```markdown
# Module Name

One-sentence purpose.

## What You'll Learn
- Concept 1
- Concept 2
- Concept 3

## Concept Overview

Why this matters. When to use it.

| Aspect | Details |
|---|---|
| **Cost** | $X per 1K calls |
| **Latency** | Y ms p99 |
| **Quality** | Z% accuracy |
| **Complexity** | Easy / Medium / Hard |

## Implementation

```python
from core.llm import chat

response = await chat([...])
```

## Tradeoffs

| Pro | Con |
|---|---|
| Fast | Expensive |
| Accurate | Slow |

## Next Steps
- [See ../adjacent-module/](../adjacent-module/)
- [Interview Q&A](../../interview-prep/system-design-questions/)

## Status
✅ Implemented | 🚧 In Progress | 📋 Planned
```

### Code Comments
Only document the WHY, not the WHAT. Good code is self-documenting.

```python
# ✅ Good: explains intent
# Use semantic cache for identical queries to save 90% cost
cached_response = await semantic_cache.get(query)

# ❌ Bad: restates code
# Get the response from semantic cache
cached = await semantic_cache.get(query)
```

---

## Cost Reporting

Every feature change must include a cost analysis:

**Format:**
```
Cost Impact:
- Per-call tokens: N → N' (Δ% change)
- Per-call cost: $X → $X' (at Anthropic Haiku rates)
- Monthly (1M users): $Y → $Y'

Example: RAG retrieval upgrade
- Before: 5K tokens, $0.004
- After: 6K tokens, $0.005
- Monthly (1M users): $4K → $5K (cost/quality tradeoff worth it)
```

---

## Adding a New Module

### 1. Create folder structure
```bash
mkdir -p new_module/{examples,tests,benchmarks}
touch new_module/__init__.py
touch new_module/README.md
```

### 2. Write README
See template above. Include purpose, concept table, examples.

### 3. Implement (following code standards)
```bash
make fmt && make lint
```

### 4. Add tests
```bash
pytest tests/ -v
```

### 5. Update root docs
- Add entry to README.md module index
- Update ROADMAP.md status
- Add entry to mkdocs `docs/nav.yml` (Phase 10)

### 6. Open PR
Follow pull request template. Include cost analysis if applicable.

---

## Review Process

### What Reviewers Look For
1. **Quality:** Runnable, tested, typed, logged
2. **Cost-consciousness:** Token usage justified
3. **Modularity:** No cross-module coupling (outside core/)
4. **Documentation:** Concept explained; tradeoffs clear
5. **Pedagogy:** Code is learning-friendly

### Responding to Feedback
- **Architecture questions:** Respond in PR; update SYSTEM_DESIGN.md if decision impacts future PRs
- **Code style:** Address immediately; use `make fmt` and commit
- **Testing:** Add test if not present
- **Documentation:** Clarify or expand

---

## Common Patterns

### Logging
```python
import structlog

log = structlog.get_logger(__name__)

log.info("event", field1=value1, field2=value2)
log.warning("something unexpected", error=str(e))
log.error("failure", exception=e, context="operation_name")
```

### Async Patterns
```python
import asyncio

# Don't block
async def fetch_many(items):
    tasks = [fetch_one(item) for item in items]
    return await asyncio.gather(*tasks)

# Batch API calls
from core.llm import batch
responses = await batch([msg1, msg2, msg3])
```

### Error Handling
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def call_api():
    return await external_api()
```

---

## Questions?

- **How do I add a new feature to an existing module?** Same as new module; update tests + README.
- **Can I use LangChain/CrewAI everywhere?** No — only in `orchestration/` and with `core/` as the LLM layer.
- **What if I disagree with a design decision?** Open an issue; discuss in PR or discussion.

---

## Recognition

Contributors are acknowledged in [CONTRIBUTORS.md](CONTRIBUTORS.md) (coming in Phase 2).

---

*Thank you for helping build the best AI engineering resource!* 🚀
