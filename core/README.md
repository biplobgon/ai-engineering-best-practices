# Core SDK

**Status:** 🚧 Phase 2 (Implementation Pending)

The `core/` package is the **single source of truth** for all shared primitives. Every other module imports from here.

## What You'll Learn

- How to build a unified LLM client across providers
- Caching strategies (exact + semantic) for cost optimization
- Observability patterns with OpenTelemetry
- Structured outputs with Pydantic + Instructor

## Architecture

```
core/
├── llm/          # LiteLLM wrapper + model router
├── cache/        # Redis exact + semantic cache
├── schemas/      # Pydantic models
├── telemetry/    # OpenTelemetry + cost metrics
├── retry/        # Tenacity policies
├── prompts/      # Template loader + versioning
├── eval/         # LLM-as-judge + RAGAS
├── guardrails/   # Input/output validation
└── config/       # Pydantic settings
```

## Design Principles

| Principle | Implementation |
|---|---|
| **Async-first** | All I/O is async; sync wrappers only at edges |
| **Cache by default** | Every LLM call checks cache first |
| **Observable** | Every call emits OTel span with tokens/cost |
| **Type-safe** | Pydantic models everywhere |
| **Cheap-first** | Router picks cheapest model by default |

## Usage Example (Phase 2)

```python
from core.llm import chat
from core.cache import semantic_cache
from core.config import settings

# High-level chat with caching + observability
response = await chat(
    messages=[{"role": "user", "content": "What is RAG?"}],
    cache=True,  # checks exact + semantic cache
)

print(response.text)
print(f"Cost: ${response.usd_cost}")
print(f"Cached: {response.cached}")
```

## Implementation Status

- [x] **Phase 1:** Interface stubs with docstrings ✅
- [ ] **Phase 2:** Full implementation (ETA: Week 2–3)
  - [ ] `llm/` — LiteLLM client + router
  - [ ] `cache/` — Redis exact + semantic
  - [ ] `telemetry/` — OTel instrumentation
  - [ ] `schemas/` — Pydantic + Instructor
  - [ ] `retry/` — Tenacity policies
  - [ ] `prompts/` — Template loader
  - [ ] `eval/` — Judge + RAGAS
  - [ ] `guardrails/` — Validators
  - [ ] `config/` — Settings
- [ ] **Phase 2:** Test suite (>80% coverage)

## Next Steps

See [ROADMAP.md — Phase 2](../ROADMAP.md#phase-2-core-sdk-implementation-) for implementation plan.
