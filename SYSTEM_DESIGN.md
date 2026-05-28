# System Design: ai-engineering-best-practices

This document describes the layered architecture, design decisions, and principles that guide the repository.

---

## Layered Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ L5 — Projects & Enterprise Case Studies                          │
│      (end-to-end systems: platform, agent, compliance)           │
├──────────────────────────────────────────────────────────────────┤
│ L4 — Domain Modules                                              │
│      (rag/, agents/, multi-agent/, orchestration/, memory/)      │
├──────────────────────────────────────────────────────────────────┤
│ L3 — Cross-Cutting Concerns                                      │
│      (evaluation/, llmops/, guardrails/, ai-security/)           │
├──────────────────────────────────────────────────────────────────┤
│ L2 — Core SDK (Shared Primitives)                                │
│      (llm/, cache/, schemas/, telemetry/, retry/, prompts/,     │
│       eval/, guardrails/, config/)                              │
├──────────────────────────────────────────────────────────────────┤
│ L1 — Infrastructure & Observability                              │
│      (Docker, Postgres+pgvector, Redis, Jaeger, MLflow)         │
└──────────────────────────────────────────────────────────────────┘
```

### Design Rules

**Rule 1: Everything imports from `core/`**
- `core/` is the single source of truth for LLM calls, caching, telemetry, schemas.
- No module (outside `core/`) directly imports OpenAI SDK, LiteLLM, or other providers.
- Enforced by CI check: `ruff` custom rule or `grep` gate.

**Rule 2: Modules are siblings, not nested**
- Each domain module (`rag/`, `agents/`, etc.) is independently navigable.
- No module depends on another domain module directly.
- Cross-cutting concerns (`evaluation/`, `llmops/`) can be shared via imports, but optional.

**Rule 3: `core/` is aggressively minimal**
- Only primitives that 3+ modules need.
- No business logic; only contracts.
- Stable interfaces: once public, changes are versioned.

**Rule 4: Async-first, with sync facades only at edges**
- All `core/` and domain logic is async.
- Sync wrappers only in FastAPI endpoints (Uvicorn handles async).
- This maximizes throughput without complexity.

**Rule 5: Everything is observable**
- Every LLM call emits an OpenTelemetry span.
- Spans include: tokens_in, tokens_out, usd_cost, latency_ms, model, cached.
- Distributed traces across service boundaries.

**Rule 6: Schema-first, not code-first**
- Pydantic models define I/O contracts.
- Instructor wraps models → auto-retry on parse failure.
- No "best-effort" JSON parsing; every output is validated.

---

## Core Module Contracts

### `core/llm` — LLM Client & Router

**Why LiteLLM?**
- One interface across OpenAI, Anthropic, Bedrock, Ollama, vLLM.
- Enables cost-based routing and fallback escalation.
- Token counting unified.

**Public API (minimum):**
```python
# Async client
async def chat(
    messages: list[Message],
    *,
    model: str | None = None,           # defaults to cheapest
    schema: type[T] | None = None,      # Pydantic model → Instructor retry
    cache: bool = True,                 # check semantic/exact cache first
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs
) -> Response:
    """
    High-level chat interface. Returns Response with metadata (tokens, cost, latency).
    Handles caching, retry, error handling, telemetry.
    """

async def stream(
    messages: list[Message],
    **kwargs
) -> AsyncIterator[Chunk]:
    """Token-by-token streaming for low-latency apps."""

async def embed(
    texts: list[str],
    model: str | None = None,
    batch_size: int = 1000
) -> list[Vector]:
    """Batch embedding with automatic batching."""

class Router:
    def choose(self, task_type: TaskType) -> ModelSpec:
        """Cheap-first routing: tries cheapest model; falls back if needed."""
```

**Why avoid vendor lock-in?**
- Model prices, performance, availability change constantly.
- Switching providers is one env-var change.
- Examples remain valid across vendors.

**Token Cost Accounting:**
- Every response includes `tokens_in`, `tokens_out`, `usd_cost`.
- Summed into `core/telemetry` meters.
- Enables per-feature cost tracking.

---

### `core/cache` — Exact & Semantic Caching

**Why Redis?**
- Sub-millisecond retrieval.
- Built-in TTL (data expiration).
- Pub/sub for invalidation.
- One service handles both cache types.

**Public API:**
```python
class ExactCache:
    """Hash of (messages, model, parameters) → cached Response."""
    async def get(self, key: str) -> Response | None
    async def set(self, key: str, value: Response, ttl: int = 3600)

class SemanticCache:
    """Query embedding → find similar cached queries (cosine similarity > threshold)."""
    async def get(self, query: str, threshold: float = 0.93) -> Response | None
    async def set(self, query: str, response: Response, ttl: int = 3600)
```

**Cost impact:**
- Semantic cache: ~0.001 tokens per cache lookup (embedding only, no LLM call).
- Exact cache: ~0 tokens (simple hash lookup).
- Eliminates duplicate queries to same LLM.

---

### `core/telemetry` — Observability

**Why OpenTelemetry?**
- Vendor-neutral (works with Jaeger, Datadog, New Relic, etc.).
- Standardized `Span` attributes.
- Extensible: custom attributes for tokens, cost, model.

**Public API:**
```python
@traced("task_name")  # decorator
async def my_function(...):
    """Automatically emits OTel span with attrs: tokens_in, tokens_out, usd_cost."""
```

**Metrics emitted:**
- `tokens_in` (counter) — cumulative input tokens
- `tokens_out` (counter) — cumulative output tokens
- `usd_cost` (counter) — cumulative cost in USD
- `latency_ms` (histogram) — response latency percentiles

**Where they go:**
- Local: Jaeger (all-in-one, see `docker-compose up`)
- Prod: Export via OTLP to your observability platform.

---

### `core/schemas` — Pydantic + Instructor

**Why Instructor?**
- Wraps Pydantic models.
- When `chat(..., schema=MyModel)` is called, Instructor auto-retries if JSON is invalid.
- Eliminates biggest hidden cost: parse-failure retries.

**Example:**
```python
from instructor import BaseModel

class Citation(BaseModel):
    text: str
    source: str
    page: int

response = await llm.chat(
    messages=[...],
    schema=Citation,  # forces valid Citation or retries
)
# response.citations: list[Citation] ✅ guaranteed valid
```

---

### `core/retry` — Tenacity Policies

**Policies:**
- `policy_standard()` — exponential backoff, max 3 retries, on 429/500/timeout.
- `policy_idempotent()` — retry only on 429 (safe to re-run).
- `policy_llm_rate_limit()` — long backoff for rate limits (2^attempt seconds).

**Where used:**
- LLM calls (automatic in `llm.chat`).
- API calls (embeddings, rerankers).
- Database operations (transient failures).

---

### `core/prompts` — Template Loader & Versioning

**Why versioning?**
- Prompt is code. Code has versions.
- Track which prompt produced which output.
- Regression detection (prompt A vs B).

**Public API:**
```python
async def load(name: str, version: str = "latest", **vars) -> str:
    """
    Load prompt by name and version.
    Templates use Jinja2: "Hello {{name}}"
    """

# Example:
prompt = await prompts.load("rag.answer_generation", version="2024-05-28", 
                             context="...", query="...")
```

**Storage:**
- File-backed: `prompts/` folder with versioned YAML files.
- Each file: name, version, content, metadata (author, updated_at, hash).
- Optional MLflow sync for full audit trail.

---

### `core/eval` — Evaluation Primitives

**LLM-as-Judge:**
```python
async def judge(
    prediction: str,
    reference: str,
    rubric: str
) -> Score:
    """Uses LLM to score prediction against reference using rubric."""
```

**RAGAS Metrics:**
```python
async def faithfulness(response: str, context: str) -> float:
    """0–1 score: does response faithfully use context?"""

async def answer_relevancy(response: str, query: str) -> float:
    """0–1 score: how well does response answer the query?"""
```

---

### `core/guardrails` — Input/Output Validation

**Input validators:**
- Length checks (context window)
- PII detection (redact SSN, email, etc.)
- Jailbreak/prompt-injection detection
- Language detection (multilingual safety)

**Output validators:**
- Hallucination detection (is output faithful to context?)
- Citation validation (are claims attributed?)
- Format validation (matches expected schema)

---

### `core/config` — Pydantic Settings

**Single source of environment config:**
```python
class Settings(BaseSettings):
    DEFAULT_LLM: str = "anthropic/claude-haiku-3-5-sonnet"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    POSTGRES_URL: str = "postgresql://..."
    LOG_LEVEL: str = "INFO"
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 86400
```

**Why?**
- Single `.env` file for all services.
- Type-safe: Pydantic validates on load.
- Defaults sensible: works without config.

---

## Token/Cost Optimization Patterns

### Pattern 1: Cheap-First Routing
```python
router.choose("classification")  # picks gpt-4o-mini
router.choose("reasoning")       # picks claude-haiku (smarter for cost)
router.choose("fallback")        # tries cheap; upgrades if fails
```

**Benefit:** ~70% cost reduction vs fixed model.

### Pattern 2: Semantic Caching
```python
response = await llm.chat(
    messages=[...],
    cache=True  # checks semantic cache before LLM call
)
```

**Benefit:** Identical/similar queries skip LLM entirely; ~99% latency reduction.

### Pattern 3: Schema-First Output
```python
class Answer(BaseModel):
    text: str
    confidence: float

response = await llm.chat(..., schema=Answer)
# Instructor auto-retries on JSON error
# No manual parsing; no error handling
```

**Benefit:** Eliminates parse-failure retries; ~15% cost reduction in many workloads.

### Pattern 4: Batching
```python
responses = await llm.batch([
    {"messages": [...], "model": "cheap"},
    {"messages": [...], "model": "cheap"},
    # ... 100 calls concurrently
])
```

**Benefit:** Parallelism; 10–100× throughput; same total cost.

### Pattern 5: Prompt Caching (Anthropic)
```python
# Long context cached at provider level
system = "You are a legal expert. Here is a 100K-token contract: {{contract}}"
response = await llm.chat(
    messages=[system + question],
    cache=True  # provider caches contract; next call reuses it
)
```

**Benefit:** 90% cost reduction on cache hits (Anthropic: $0.30/1M input tokens vs $3/1M prompt cache).

---

## Observability Strategy

### Three Levels of Tracing

**L1: Span-level (every LLM call)**
- Span name: "llm.chat" or "vector_db.search"
- Attributes: tokens, cost, model, cache hit, latency

**L2: Task-level (business logic)**
- Span name: "answer_user_query" or "search_knowledge_base"
- Child spans: retrieve, rank, generate, validate

**L3: Request-level (API boundary)**
- Span name: "POST /api/chat"
- Headers: trace-id for distributed tracing

**Output:** Jaeger UI shows full request waterfall; identify bottlenecks instantly.

---

## Module Dependencies (Import Graph)

```
core/              (no imports outside core)
├── config         (← all modules)
├── llm            (← core/cache, core/telemetry, core/retry, core/schemas)
├── cache          (← core/llm, core/telemetry, core/config)
├── telemetry      (← core/config)
├── schemas        (← all modules)
├── retry          (← core/llm)
├── prompts        (← core/config)
├── eval           (← core/llm, core/schemas)
└── guardrails     (← core/schemas, core/telemetry)

L3 modules (evaluation/, llmops/, guardrails/)
├── import core/*
├── may import each other
└── do NOT import L4 (domain) modules

L4 modules (rag/, agents/, multi-agent/)
├── import core/*
├── import L3 (evaluation/, guardrails/)
└── do NOT import each other

L5 (projects/)
└── imports L4 + L3 + core (orchestrates everything)
```

**Enforcement:** CI check runs `ruff` with custom rule; fails if core/llm/sdk is imported outside core/.

---

## Decision Records (ADRs)

### ADR-001: Use uv instead of Poetry

**Decision:** uv only. No Poetry fallback.

**Rationale:**
- 10–100× faster dependency resolution.
- Single `pyproject.toml` → simpler automation.
- Becoming Python ecosystem standard (alongside pip-tools).

**Alternatives Considered:**
- Poetry: slower, heavier, redundant.
- pip-tools: more manual; uv is modern successor.

---

### ADR-002: LiteLLM as Primary LLM Client

**Decision:** LiteLLM wraps all LLM SDK calls.

**Rationale:**
- One interface across OpenAI, Anthropic, Bedrock, Ollama.
- Enables router (cheap → fallback).
- Token counting unified.

**Alternatives Considered:**
- Direct OpenAI SDK: locks to OpenAI (false economy).
- LangChain: broader scope; we use it only for document loaders.

---

### ADR-003: pgvector as Primary Vector Store

**Decision:** pgvector + Postgres for all examples; Qdrant optional comparison.

**Rationale:**
- One database for metadata + vectors → simpler ops.
- Open source, self-hosted, no vendor lock.
- Sufficient performance for most enterprises.

**Alternatives Considered:**
- Pinecone: convenient, but expensive + vendor lock.
- Qdrant: pure vector DB; heavier ops for metadata joins.

---

### ADR-004: Instructor for Structured Outputs

**Decision:** Instructor + Pydantic v2 for all JSON-generating tasks.

**Rationale:**
- Auto-retry on parse failure → eliminates biggest hidden cost.
- Type safety + validation.
- Cleaner code than manual JSON parsing + error handling.

**Alternatives Considered:**
- Raw JSON mode: brittle, requires manual fallback.
- dataclasses: no validation.

---

### ADR-005: OpenTelemetry for Observability

**Decision:** OpenTelemetry (vendor-neutral) over LangSmith/custom tracing.

**Rationale:**
- Vendor-neutral; export to Jaeger, Datadog, New Relic, etc.
- CNCF standard; long-term stable.
- Optional LangSmith integration (not required).

**Alternatives Considered:**
- LangSmith: excellent but locks to LangChain ecosystem.
- Custom logging: insufficient for distributed tracing.

---

### ADR-006: LangGraph Only for Orchestration (not LangChain globally)

**Decision:** LangGraph for stateful workflows; skip LangChain for most use cases.

**Rationale:**
- LangChain adds abstraction tax (token bloat, slower).
- Native implementations in `agents/` are clearer.
- LangGraph's state machines are genuinely useful.

**Alternatives Considered:**
- LangChain everywhere: bloated examples, hard to optimize.
- No framework: LangGraph solves real stateful workflow problems.

---

### ADR-007: Anthropic Claude Haiku as Default Model

**Decision:** Anthropic Claude Haiku (via LiteLLM) as default; OpenAI as fallback.

**Rationale:**
- Haiku: cheapest reliable reasoning model ($0.80/1M input tokens).
- Prompt caching available (90% cheaper on cache hits).
- Examples run for ~$0 in fixture scenarios.

**Alternatives Considered:**
- OpenAI GPT-4o-mini: more expensive; better marketing.
- Local Ollama: less representative of enterprise use.

---

### ADR-008: Single Docker Compose for Local Dev

**Decision:** One `docker-compose.yml` with all services (Redis, Postgres+pgvector, Jaeger, MLflow).

**Rationale:**
- Zero-setup onboarding: `make up && make test`.
- Optional profiles (`--profile rag`) for minimal footprint.
- Matches production architecture.

**Alternatives Considered:**
- Manual Docker commands: repetitive, error-prone.
- Multiple compose files: fragmented.

---

## Scalability Considerations

### Horizontal Scaling

**LLM Calls:**
- Async/await → single machine handles 100s concurrent calls.
- Scale with worker pool (Celery) when needed.

**Vector Search:**
- pgvector indexes scale to 10B+ vectors with proper tuning.
- Horizontal scaling via partitioning (by customer_id, region, etc.).

**Caching:**
- Redis Cluster for HA + sharding.
- Semantic cache: pre-compute embeddings; cache hit rate 70–90%.

---

### Cost Scaling

**1M users, 10M calls/month:**
- Default routing: ~$1–2K/month (Anthropic).
- With semantic cache: ~$500–1K/month (70% cache hit rate).
- With prompt caching: ~$200–500/month (90% cache hit rate).

**10M users, 100M calls/month:**
- Dedicated model hosting (Ollama, vLLM): ~$3–5K/month.
- Batching + async: 10× throughput improvement.

---

## Security & Governance

### PII & Data Governance
- Input validation: detect and redact PII.
- Output validation: ensure citations, no data leakage.
- Audit logs: Postgres logs all requests (for compliance).

### Prompt Injection Defense
- Input length limits.
- Jailbreak detection (heuristics + LLM-based).
- Schema enforcement (no freeform output).

### Model & API Security
- API keys: never in code; `.env` only (local) or secrets manager (prod).
- Rate limiting: per-user quotas (Redis).
- Audit trail: trace-id links requests to users.

---

## Performance Benchmarks (Baseline)

| Operation | Latency (p99) | Cost |
|---|---|---|
| LLM chat (cold) | 500ms | $0.01 |
| LLM chat (exact cache hit) | 5ms | $0 |
| LLM chat (semantic cache hit) | 50ms | $0.0001 |
| Vector search (pgvector) | 20ms | $0 |
| Embedding (1K vectors) | 500ms | $0.001 |
| Full RAG pipeline (retrieve + rank + generate) | 800ms | $0.02 |

---

## Continuous Improvement

### Metrics to Track
- **Cost per outcome:** $/successful query.
- **Cache hit rate:** % of queries avoided via cache.
- **Latency p99:** response time 99th percentile.
- **Eval score:** accuracy, faithfulness, hallucination rate.

### Feedback Loop
1. Ship feature with evals in CI.
2. Monitor cost/quality in prod.
3. Iterate prompts + retrieval + model.
4. Update regression suite.

---

## Next: Phase 2 Entry

Ready to implement `core/`? See [ROADMAP.md — Phase 2](ROADMAP.md#phase-2-core-sdk-implementation-).
