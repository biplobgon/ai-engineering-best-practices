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
- [x] **Phase 2:** Full implementation ✅ **COMPLETE**
  - [x] `llm/` — LiteLLM client + router ✅
  - [x] `cache/` — Redis exact + semantic ✅
  - [x] `telemetry/` — OTel instrumentation ✅
  - [x] `schemas/` — Pydantic + Instructor ✅
  - [x] `retry/` — Tenacity policies ✅
  - [x] `prompts/` — Template loader ✅
  - [x] `eval/` — Judge + RAGAS ✅
  - [x] `guardrails/` — Validators ✅
  - [x] `config/` — Settings ✅
- [x] **Phase 2:** Test suite ✅

## Quick Start

```bash
# Install dependencies
make install

# Start services (Redis, Postgres, Jaeger)
docker-compose up -d

# Set API keys in .env
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY or OPENAI_API_KEY

# Run example
python examples/basic_usage.py

# Run tests
make test
```

## Example Usage

```python
from core.llm import chat, router
from core.config import get_settings

# Basic chat
response = await chat([
    {"role": "user", "content": "What is RAG?"}
])

print(response.text)
print(f"Cost: ${response.usd_cost:.6f}")
print(f"Tokens: {response.total_tokens}")

# Model routing (cheap-first)
model = router.choose("classification")  # Uses cheapest model
print(f"Chosen: {model}")
```

## What's Ready Now

✅ **All 9 core modules fully implemented**
✅ **Production-ready with error handling, logging, retries**
✅ **Token + cost tracking built-in**
✅ **OpenTelemetry tracing integrated**
✅ **Test suite with >15 tests**
✅ **Example scripts** (see `examples/basic_usage.py`)

## Next Steps

- **Phase 3:** Pedagogy modules (fundamentals, prompt-engineering, optimization)
- See [ROADMAP.md — Phase 3](../ROADMAP.md#phase-3-pedagogy-modules-) for details
