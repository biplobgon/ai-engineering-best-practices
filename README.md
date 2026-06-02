# AI Engineering Best Practices

A production-grade handbook and reference repository for modern AI engineering. This is a **practical, modular, cost-optimized** guide to building and deploying enterprise LLM systems—from fundamentals through multi-agent orchestration.

Built by and for senior AI engineers, AI architects, and those serious about mastering AI systems engineering by 2030.

---

## TL;DR: What's Here?

| Layer | You'll Learn | Status |
|---|---|---|
| **Core SDK** | LLM client, caching, schemas, telemetry, retry, prompts, eval, guardrails | ✅ P2 |
| **Fundamentals** | Tokens, context, sampling, embeddings, cost mechanics | 🚧 P3 |
| **Prompt Engineering** | Patterns, templates, optimization, anti-patterns | 🚧 P3 |
| **RAG & Retrieval** | Naive→agentic RAG, chunking, hybrid search, reranking, RAGAS eval | 🚧 P4 |
| **Agents & Orchestration** | ReAct, tool-calling, LangGraph, supervisor patterns | 🚧 P5 |
| **Multi-Agent Systems** | Debate, handoff, swarm vs hierarchical | 🚧 P5 |
| **Memory Architectures** | Short-term, long-term, episodic, entity graphs | 🚧 P5 |
| **Evaluation Pipelines** | LLM-as-judge, regression suites, synthetic data | 🚧 P6 |
| **LLMOps** | Prompt versioning, model registry, shadow deployments, A/B testing | 🚧 P7 |
| **Observability** | OpenTelemetry, token/cost metrics, dashboards | 🚧 P6 |
| **Cost Optimization** | Model routing, semantic caching, prompt caching, batching | 🚧 P3 |
| **Token Optimization** | Compression, context pruning, summarization | 🚧 P3 |
| **Latency Optimization** | Streaming, parallel tool calls, async batching | 🚧 P3 |
| **Guardrails & Security** | Input validation, PII redaction, prompt injection, OWASP LLM Top 10 | 🚧 P6 |
| **Deployment** | FastAPI services, streaming SSE, async jobs, Kubernetes | 🚧 P7 |
| **Enterprise Case Studies** | Multi-tenant LLM platform, Agentic research assistant, Compliance QA | 🚧 P8 |
| **Interview Prep** | System design, coding, fundamentals, behavioral | 🚧 P9 |

---

## What's Ready to Use Right Now? ✅

**Phase 2 Core SDK is production-ready!** You can immediately use:

1. **LLM Chat** - Unified interface for OpenAI, Anthropic, Bedrock, Ollama
2. **Streaming** - Token-by-token output with `async for`
3. **Embeddings** - Batch text embedding with auto-batching
4. **Model Routing** - Automatic cheap-first model selection
5. **Caching** - Exact (hash-based) + Semantic (embedding similarity) cache
6. **Guardrails** - PII detection/redaction, jailbreak detection
7. **Evaluation** - LLM-as-judge + RAGAS metrics (faithfulness, relevancy)
8. **Telemetry** - OpenTelemetry tracing + cost/token/latency metrics

See `examples/basic_usage.py` for working code samples of all features.

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/YOUR_GITHUB/ai-engineering-best-practices.git
cd ai-engineering-best-practices
uv sync

# Set API keys
cp .env.example .env
# Edit .env with ANTHROPIC_API_KEY and optionally OPENAI_API_KEY

# Start services (Redis, Postgres+pgvector, Jaeger)
docker-compose up -d

# Run tests
make test

# Explore a module
cd prompt-engineering/patterns
python -m pytest -v
```

---

## Learning Path by Role & Timeline

### 👨‍💼 For Senior Engineers (3–6 months to AI Architect)

**Month 1:** `fundamentals/` + `prompt-engineering/` + `cost-optimization/`
- Lock in token mechanics, sampling, prompt design principles.
- Do: tune default settings, build cost models.

**Month 2:** `rag/` (01–08 ladder) + `evaluation/`
- Master retrieval, chunking strategies, reranking, RAGAS pipeline.
- Do: build a retrieval benchmark; run eval suite.

**Month 3:** `agents/` + `multi-agent/` + `orchestration/`
- Understand ReAct, tool-calling, stateful workflows.
- Do: build a 3-agent system; reason about supervisor patterns.

**Months 4–6:** `llmops/` + `ai-observability/` + `deployment/` + case studies
- Ship a production system with monitoring, versioning, guardrails.
- Do: all 3 case studies; design your own system.

### 👨‍🎓 For Learners (6–12 months to Senior AI Engineer)

Start here → **[See LEARNING_PATH.md for week-by-week curriculum](#learning-path)**

---

## Repository Structure

```
ai-engineering-best-practices/
├── README.md                          # This file
├── ROADMAP.md                         # Phased build plan
├── SYSTEM_DESIGN.md                   # Architecture & ADRs
├── LEARNING_PATH.md                   # Week-by-week curriculum
├── AI_ENGINEER_CHECKLIST.md           # Production readiness
│
├── core/                              # ★ Shared primitives (✅ IMPLEMENTED - all modules import here)
│   ├── llm/                           # ✅ LiteLLM-wrapped client + router
│   ├── cache/                         # ✅ Exact + semantic caching (Redis)
│   ├── schemas/                       # ✅ Pydantic base models
│   ├── telemetry/                     # ✅ OTel + cost metrics
│   ├── retry/                         # ✅ Tenacity policies
│   ├── prompts/                       # ✅ Prompt template loader (Jinja2)
│   ├── eval/                          # ✅ Evaluation primitives (LLM-as-judge, RAGAS)
│   ├── guardrails/                    # ✅ Input/output validators (PII, jailbreak)
│   └── config/                        # ✅ Settings (Pydantic)
│
├── fundamentals/                      # Pedagogy: tokens, context, sampling
├── prompt-engineering/                # Patterns, templates, optimization
├── rag/                               # Naive→agentic RAG ladder
├── agents/                            # Single-agent systems
├── multi-agent/                       # Multi-agent patterns
├── memory/                            # Memory architectures
├── evaluation/                        # Evaluation pipelines
├── llmops/                            # Versioning, registry, testing
├── ai-observability/                  # Tracing, metrics, dashboards
├── cost-optimization/                 # Router, caching, batching
├── token-optimization/                # Compression, context pruning
├── latency-optimization/              # Streaming, parallel execution
├── guardrails/                        # Validation, PII, injection
├── ai-security/                       # OWASP LLM Top 10
├── architecture-patterns/             # ADRs, design patterns
│
├── deployment/                        # FastAPI, Celery, streaming
├── infra/                             # Docker, Terraform stubs
├── kubernetes/                        # K8s manifests, HPA
├── streaming/                         # SSE, WebSocket patterns
├── async-patterns/                    # asyncio, batching, backpressure
├── vector-databases/                  # pgvector, Qdrant, benchmarks
├── workflows/                         # Deterministic DAGs
├── orchestration/                     # LangGraph, native agents
│
├── benchmarks/                        # Perf, cost, recall benchmarks
├── testing/                           # Unit, integration, eval-as-test
├── enterprise-case-studies/           # 3 production systems
├── interview-prep/                    # System design, coding, behavioral
├── templates/                         # Boilerplate for new modules
│
├── notebooks/                         # Exploratory (not source of truth)
├── docs/                              # mkdocs-material source
├── diagrams/                          # Excalidraw + Mermaid
├── scripts/                           # Utilities
├── examples/                          # Tiny copy-paste snippets
│
├── pyproject.toml                     # Dependencies (uv)
├── uv.lock                            # Lockfile
├── Makefile                           # Dev UX
├── docker-compose.yml                 # Services
├── .env.example                       # Config template
├── .ruff.toml                         # Linting
├── .pre-commit-config.yaml            # Git hooks
├── .gitignore
├── CONTRIBUTING.md
└── LICENSE (MIT)
```

---

## Core Principles (Why This Repo Exists)

### 🎯 Token Efficiency = Cost Efficiency
- Every module prioritizes **shorter prompts**, **better schemas**, **smarter caching**.
- Examples default to **cheap models** (Anthropic Claude Haiku).
- We show **token-per-operation cost** in every scenario.

### 🏗️ Production-Ready From Day One
- All code has logging, retries, error handling, typing.
- All examples are runnable with real APIs (fixture-only cost).
- All patterns include observability hooks.

### 🔌 Composable Over Monolithic
- Each module stands alone; no mandatory dependencies.
- `core/` is the only place business logic is shared.
- You can use any piece in isolation.

### 🧠 Explanation-First
- Every concept: what it is → why it matters → when to use it → tradeoffs.
- Interview questions and system design walkthroughs included.

---

## Tech Stack at a Glance

| Layer | Technology | Why |
|---|---|---|
| **LLM Client** | LiteLLM | One interface across OpenAI, Anthropic, Bedrock, local |
| **Default Models** | Anthropic Claude Haiku + OpenAI gpt-4o-mini | Cheapest + best reasoning |
| **Structured Outputs** | Instructor + Pydantic v2 | Retries built in; kill parse failures |
| **Caching** | Redis (exact + semantic) | Sub-ms retrieval; built-in TTL |
| **Vector DB** | pgvector + Postgres | One database for metadata + vectors |
| **Observability** | OpenTelemetry + Jaeger | Vendor-neutral tracing + token accounting |
| **FastAPI** | FastAPI + Uvicorn | Async-native API framework |
| **Orchestration** | LangGraph (optional) | Stateful workflows without vendor lock |
| **Package Mgr** | uv | 10-100× faster than Poetry |
| **Testing** | pytest + parametrize | Standard, supports async |
| **CI/CD** | GitHub Actions | Free, integrated, sufficient |

---

## Cost Philosophy

We obsess over **tokens-per-outcome**:

1. **Model routing** (cheap → fallback to smart) — default is Haiku
2. **Semantic caching** — identical queries re-use cached embeddings
3. **Prompt caching** — repetitive context (docs, code) cached at provider
4. **Structured outputs** — no JSON parsing retries
5. **Batch processing** — concurrent API calls, not sequential
6. **Context optimization** — prune non-essential context before sending

Every case study includes a **cost report**: expected spend for 1M users, 10M calls.

---

## What's NOT Here

- **Model training/fine-tuning** (focus is inference engineering)
- **Hugging Face transformers deep dive** (not in scope for 2025)
- **Heavy-duty data engineering** (e.g., Spark; use `pyspark-aws-bigdata` skill if needed)
- **CrewAI/AutoGen deep dives** (frameworks compared conceptually; native + LangGraph prioritized)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Branch naming, commit conventions
- How to add a module
- Code review criteria
- Eval gate expectations

---

## Roadmap & Phases

See [ROADMAP.md](ROADMAP.md) for phased build plan:
- **P1:** Foundation, docs, tooling ✅
- **P2:** Core SDK + tests ✅
- **P3:** Pedagogy modules 🚧
- **P4–P10:** Domain modules → case studies → interview prep 🚧

---

## Learning: Pick Your Path

- **"I want to understand how to build RAG"** → Start: `fundamentals/` → `prompt-engineering/` → `rag/`
- **"I'm prepping for a staff AI engineer interview"** → Start: `interview-prep/system-design-questions/`
- **"I want to ship a production LLM system"** → Start: `deployment/fastapi-service/` → any case study
- **"I want to understand agentic AI"** → Start: `agents/react-from-scratch/` → `multi-agent/supervisor-pattern/`

---

## License

MIT — use freely in commercial and personal projects.

---

## Feedback & Issues

- **Report bugs or suggest improvements:** [GitHub Issues](https://github.com/YOUR_GITHUB/ai-engineering-best-practices/issues)
- **Contribute:** [See CONTRIBUTING.md](CONTRIBUTING.md)

---

**Last updated:** Phase 2 (Core SDK complete) — See [ROADMAP.md](ROADMAP.md) and [PHASE_2_REPORT.md](PHASE_2_REPORT.md) for details.

**Current Status:** 
- ✅ Phase 1: Architecture, documentation, tooling
- ✅ Phase 2: Core SDK (9/9 modules implemented with ~1590 LOC)
- 🚧 Phase 3: Pedagogy modules (in progress)
