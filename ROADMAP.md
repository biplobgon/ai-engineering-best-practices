# Roadmap: ai-engineering-best-practices

This document tracks the phased build of the repository. Each phase gates the next; completion means runnable, tested, documented.

---

## Phase Status Overview

| Phase | Scope | Deliverables | Target | Status |
|---|---|---|---|---|
| **P1** | Foundation, docs, tooling | README, ROADMAP, SYSTEM_DESIGN, LEARNING_PATH, folder skeleton, pyproject.toml, docker-compose, CI stubs, core/ interface | Wk 1 | ✅ **ACTIVE** |
| **P2** | Core SDK implementation | llm client + router, cache (exact+semantic), telemetry, prompts, schemas, retry, guardrails, config | Wk 2–3 | 🚧 Pending |
| **P3** | Pedagogy (token/cost/latency basics) | fundamentals/, prompt-engineering/, cost-optimization/, token-optimization/, latency-optimization/ | Wk 4–5 | 🚧 Pending |
| **P4** | RAG full stack | rag/ (01–08 ladder), vector-databases/ benchmarks, evaluation/ (RAGAS) | Wk 6–8 | 🚧 Pending |
| **P5** | Agents + multi-agent + orchestration | agents/ (ReAct, tool-calling), multi-agent/ (patterns), orchestration/ (LangGraph) | Wk 9–11 | 🚧 Pending |
| **P6** | Quality & observability | evaluation/ (LLM-as-judge), ai-observability/ (OTel, dashboards), guardrails/, ai-security/ | Wk 12–14 | 🚧 Pending |
| **P7** | Production deployment | deployment/ (FastAPI, streaming, Celery), kubernetes/, infra/ (Docker, Terraform stubs) | Wk 15–17 | 🚧 Pending |
| **P8** | Enterprise case studies | 3 full systems: multi-tenant platform, agentic research assistant, compliance doc QA | Wk 18–21 | 🚧 Pending |
| **P9** | Interview prep + learning roadmap | interview-prep/ (system design, coding, ML fundamentals, behavioral), Senior→Architect curriculum | Wk 22–24 | 🚧 Pending |
| **P10** | Polish + docs site | mkdocs-material build, diagrams (Excalidraw), benchmarks, examples gallery, deploy to GitHub Pages | Wk 25–26 | 🚧 Pending |

---

## Phase 1: Foundation ✅ (In Progress)

### Scope
- Architecture finalized and documented
- Folder structure created
- Tooling configured
- Core module interfaces stubbed (signatures only)
- CI/CD skeleton in place
- Root documentation complete

### Deliverables

**Root documentation** (6 files):
- ✅ `README.md` — hero doc, TL;DR, quick start, learning paths
- 🚧 `ROADMAP.md` — this file
- 🚧 `SYSTEM_DESIGN.md` — layered architecture, ADRs, design principles
- 🚧 `LEARNING_PATH.md` — week-by-week curriculum (0→senior→architect)
- 🚧 `AI_ENGINEER_CHECKLIST.md` — production readiness checklist
- 🚧 `CONTRIBUTING.md` — dev guidelines, PR template

**Tooling** (8 files):
- 🚧 `pyproject.toml` — uv-managed, Python 3.12+, grouped dependencies
- 🚧 `uv.lock` — lockfile
- 🚧 `.ruff.toml` — linting rules
- 🚧 `.pre-commit-config.yaml` — git hooks
- 🚧 `Makefile` — dev UX (`make install`, `make test`, etc.)
- 🚧 `docker-compose.yml` — Redis, Postgres+pgvector, Jaeger, MLflow
- 🚧 `.env.example` — config template
- 🚧 `.gitignore` — standard Python/Node ignores

**GitHub** (3 files):
- 🚧 `.github/workflows/ci.yml` — lint + test + import-boundary check
- 🚧 `.github/workflows/eval-gate.yml` — placeholder (activated in P6)
- 🚧 `.github/PULL_REQUEST_TEMPLATE.md` — PR checklist

**Folder skeleton** (40+ folders):
- Each top-level module gets a concise `README.md`:
  - 1-line purpose
  - "What you'll learn" (3 bullets)
  - Tradeoff/concept table (placeholder)
  - Phase status badge (e.g., `🚧 P4`)
- `core/` gets full interface stubs (class + method signatures, docstrings, `NotImplementedError`)

**Misc** (3 files):
- 🚧 `LICENSE` — MIT
- 🚧 `.editorconfig` — indentation rules
- 🚧 `SYSTEM_DESIGN.md` — architecture + ADR index

### Success Criteria
- [ ] All 70+ files created (docs + config + stubs)
- [ ] `make test` runs (finds pytest, runs 0 tests, no errors)
- [ ] `docker-compose up -d` starts all services
- [ ] `make lint` runs ruff without import-boundary failures
- [ ] `pyproject.toml` dependencies are minimal and correct
- [ ] No LLM calls required; validates without external APIs

### Blockers
None. Phase 1 is pure infrastructure.

---

## Phase 2: Core SDK Implementation 🚧

### Scope
- Implement `core/` module end-to-end
- All shared primitives: LLM client, caching, telemetry, schemas, retry, prompts, eval, guardrails, config
- Full test suite for core
- No business logic in domain modules yet

### Deliverables

**`core/llm/`** (LiteLLM wrapper + router)
- `async_client()` → AsyncOpenAI-like interface wrapping LiteLLM
- `chat(messages, model=None, schema=None, cache=True)` → Response with token/cost attrs
- `stream(messages, ...) → AsyncIterator[Chunk]`
- `router.choose(task_type) → ModelSpec` (cheap-first routing)
- `embed(texts) → list[Vector]` (with batch support)
- Full error handling + retry logic (tenacity)
- OTel span decoration

**`core/cache/`** (Redis-backed)
- `ExactCache.get/set(key) → Optional[Response]`
- `SemanticCache.get/set(query, threshold=0.93) → Optional[Response]`
- TTL + invalidation helpers
- Batch clear operations

**`core/telemetry/`** (OTel + cost metrics)
- `@traced(span_name)` decorator → auto-emits OpenTelemetry spans
- Attributes: `tokens_in`, `tokens_out`, `usd_cost`, `latency_ms`, `model`, `cached`
- `MeterProvider` for Prometheus-style metrics
- Optional LangSmith integration

**`core/schemas/`** (Pydantic + Instructor helpers)
- `BaseModel` with JSON schema validation
- `InstructorModel` wrapper → auto-retries on parse failure
- Common schemas: Message, Response, ToolCall, FunctionCall

**`core/retry/`** (Tenacity policies)
- `policy_standard()` — exponential backoff, 3 retries
- `policy_idempotent()` — only on 429/500
- `policy_llm_rate_limit()` — long backoff for rate limits

**`core/prompts/`** (Template loader + versioning)
- `load(name, version="latest", **vars) → str`
- File-backed (YAML or Markdown), hashed for change detection
- MLflow sync optional
- Versioning helpers

**`core/eval/`** (Evaluation primitives)
- `judge(prediction, reference, rubric) → Score` (LLM-as-judge)
- `ragas_faithfulness(response, context) → float`
- `ragas_answer_relevancy(response, query) → float`
- Batch scoring

**`core/guardrails/`** (Input/output validation)
- `validate_input(text) → Result` (PII detection, jailbreak check, length)
- `validate_output(text, policy) → Result` (hallucination check, citation validation)
- Extensible rule engine

**`core/config/`** (Pydantic settings)
- `Settings` from `.env` or environment
- Defaults: `DEFAULT_LLM=anthropic/claude-haiku-3`, `CACHE_TTL=86400`, etc.
- Per-environment configs (dev/staging/prod)

**Tests** (pytest suite for all `core/` modules)
- Unit tests for each submodule
- Integration tests (Redis + Postgres mock)
- Cost accounting tests

### Success Criteria
- [ ] All `core/` submodules fully implemented
- [ ] `pytest core/` runs and passes (>80% coverage)
- [ ] `make up && make test` works end-to-end
- [ ] Zero external API calls required (all mocked)
- [ ] Token/cost metrics emitted from every LLM call
- [ ] Import-boundary CI check passes (no module imports external SDK)

---

## Phase 3: Pedagogy Modules 🚧

### Scope
Teach the absolute fundamentals + optimization basics.

**fundamentals/**
- 01-llm-basics: What is a token? How does sampling work?
- 02-tokens-and-cost: Token counting, pricing, cost calculation
- 03-sampling-params: Temperature, top_p, max_tokens, stop sequences
- 04-context-windows: Context limits, sliding windows, context management
- 05-embeddings: Dense vectors, similarity search, embedding costs

**prompt-engineering/**
- patterns/: Zero-shot, few-shot, CoT, ReAct, self-consistency
- templates/: Reusable, versioned prompts (meta-prompts, system messages)
- optimization/: Token reduction, prompt compression, auto-prompt tuning
- anti-patterns/: What NOT to do (verbose instructions, ambiguity, etc.)

**cost-optimization/**
- model-routing/: Cheap-first architectures with fallback escalation
- batching/: Concurrent API calls, embed batching
- semantic-cache/: Skip LLM calls for similar queries
- prompt-caching/: Vendor prompt caching (Anthropic, OpenAI)

**token-optimization/**
- compression/: Summarization pipelines, token pruning
- context-pruning/: Keep only relevant documents
- summarization-pipelines/: Reduce long docs to key facts

**latency-optimization/**
- streaming/: Token-by-token output (SSE, WebSocket)
- speculative-decoding-notes/: Conceptual overview (implementation in deployment/)
- parallel-tool-calls/: Concurrent tool execution

### Deliverables (per module)
- `README.md` with concept explanation + tradeoff table
- `examples/` folder with 2–3 runnable snippets
- `benchmark/` (if applicable): cost/latency/quality comparisons
- `tests/` with assertions on expected behavior
- One small Jupyter notebook (exploratory)

### Success Criteria
- [ ] All 5 pedagogy modules complete
- [ ] Each has ≥2 runnable examples using `core/` (no SDK calls outside)
- [ ] Cost reports in each (`N tokens → $X`)
- [ ] 🚧 Planned badges updated to ✅
- [ ] Examples run without real API calls (mocked responses)

---

## Phase 4: RAG Full Stack 🚧

### Scope
Comprehensive retrieval architecture, from naive to agentic RAG.

**rag/**
- 01-naive-rag/: Simple embed + retrieve + prompt (the baseline)
- 02-chunking-strategies/: Token-aware chunking, overlap strategies, semantic chunks
- 03-hybrid-retrieval/: BM25 + dense + RRF (Reciprocal Rank Fusion), why each matters
- 04-rerankers/: Reranking logic, cost/quality tradeoffs (cohere, etc.)
- 05-query-rewriting/: Query expansion, decomposition, rephrasing for better retrieval
- 06-graph-rag/: Knowledge graphs + entity extraction
- 07-agentic-rag/: RAG agent that decides whether to retrieve
- 08-eval-ragas/: RAGAS pipeline (faithfulness, answer_relevancy, context_precision)

**vector-databases/**
- pgvector/: Setup, indexing, performance tuning
- qdrant/ (optional): Comparison, when to use it
- pinecone-notes.md: Why we default to pgvector instead
- benchmark/: Recall vs latency vs cost matrix

**evaluation/**
- llm-as-judge/: Rubric-based scoring, GPT-as-grader
- ragas-pipelines/: RAGAS configs, debugging eval
- regression-suites/: Snapshot testing for prompts/outputs
- synthetic-eval-sets/: Generate synthetic Q&A for evaluation

### Success Criteria
- [ ] All 8 RAG levels complete with runnable examples
- [ ] RAGAS eval suite integrated into `core/eval/`
- [ ] Vector DB benchmark (recall/latency/cost matrix) published
- [ ] At least 2 enterprise-scale eval suites (100+ test cases)

---

## Phase 5: Agents + Multi-Agent 🚧

### Scope
Agent systems: single → multi.

**agents/**
- react-from-scratch/: ReAct loop (think → act → observe), no framework
- tool-calling/: OpenAI tools API, function calling, structured tool use
- planning-agents/: Plan-execute-verify loop, agent planning strategies
- reflection-agents/: Self-correction, multi-turn reasoning

**multi-agent/**
- supervisor-pattern/: One agent routes to many specialists
- debate-pattern/: Agents argue both sides; human/model decides
- handoff-pattern/: Agent hands off to next agent; state passing
- swarm-vs-hierarchical/: Comparison, when to use each

**orchestration/**
- langgraph-examples/: LangGraph state machines, checkpoint patterns
- native-comparison/: Building orchestration without frameworks
- graph-visualization/: How to visualize agent workflows

### Success Criteria
- [ ] ReAct working end-to-end without framework
- [ ] Supervisor pattern with 3+ specialist agents
- [ ] LangGraph state machine example
- [ ] Multi-agent case study (Agentic Research Assistant) design doc complete

---

## Phase 6: Quality & Observability 🚧

### Scope
Evaluation, tracing, guardrails, security.

**ai-observability/**
- otel-tracing/: Full end-to-end trace instrumentation
- token-cost-metrics/: Prometheus metrics for tokens/cost/latency
- dashboards/: Grafana JSON for cost monitoring, latency heatmaps

**guardrails/**
- input-validation/: Length, language, format checks
- output-validation/: Hallucination checks, citation validation
- pii-redaction/: PII detection + masking
- jailbreak-detection/: Prompt injection detection

**ai-security/**
- prompt-injection/: Examples + defenses
- data-exfiltration/: Preventing unintended context leakage
- owasp-llm-top10/: Mapping OWASP top 10 to our patterns

**architecture-patterns/**
- adrs/: Architecture Decision Records (why we chose uv, LiteLLM, pgvector, etc.)
- patterns/: Design patterns for AI systems (fan-out, saga, CQRS-for-AI, etc.)

### Success Criteria
- [ ] Full OTel instrumentation in deployment service
- [ ] Cost dashboards for all case studies
- [ ] PII redaction tested on common datasets
- [ ] Eval-gate CI check implemented

---

## Phase 7: Production Deployment 🚧

### Scope
Shipping to production.

**deployment/**
- fastapi-service/: Reference LLM service (chat endpoint, streaming, async jobs)
- streaming-sse/: Server-Sent Events implementation
- celery-async-jobs/: Async job queue for long-running evals

**infra/**
- docker/: Dockerfiles (service, workers, monitoring)
- terraform-stubs/: CloudFormation/Terraform examples (AWS, GCP)

**kubernetes/**
- manifests/: K8s Deployments, Services, ConfigMaps
- helm-chart/: Helm chart for easy deployment
- hpa-gpu-notes.md: Horizontal Pod Autoscaling for GPUs

### Success Criteria
- [ ] FastAPI service with `/chat` endpoint + `/stream` endpoint
- [ ] Load test results (throughput, latency p99)
- [ ] Docker image builds and runs
- [ ] K8s deployment manifest tested locally (kind or minikube)

---

## Phase 8: Enterprise Case Studies 🚧

### Scope
3 production-grade end-to-end systems.

**enterprise-case-studies/**

1. **multi-tenant-llm-platform/**
   - FastAPI gateway + API-key auth + per-tenant quotas (Redis token bucket)
   - Model routing (cheap → smart fallback)
   - Semantic caching + prompt caching
   - Usage ledger (Postgres) + cost dashboard
   - Full eval suite + regression gates
   - Cost report: $X per 1M calls @ 10K users

2. **agentic-research-assistant/**
   - LangGraph supervisor → web search + RAG tools + summarizer
   - Reflection + multi-turn reasoning
   - Episodic memory (Postgres)
   - Citation-grounded output (Instructor)
   - Faithfulness eval harness
   - Cost report: $Y per research query

3. **financial-compliance-doc-qa/**
   - Async ingestion (Celery) + hybrid retrieval (BM25 + pgvector + reranker)
   - Structured citation output (Instructor)
   - PII redaction + audit log
   - LLM-as-judge regression gate
   - Cost report: $Z per 1M queries

### Success Criteria
- [ ] All 3 case studies fully implemented
- [ ] Each has architecture diagram + cost report
- [ ] Each passes eval suite in CI
- [ ] End-to-end demo script for each

---

## Phase 9: Interview Prep + Mastery Roadmap 🚧

### Scope
Career acceleration material.

**interview-prep/**
- system-design-questions/: 10+ questions with solution walkthroughs
- coding-rounds/: LeetCode-style + LLM-specific coding challenges
- ml-llm-fundamentals/: Sampling, embeddings, retrieval, ranking
- behavioral-staff-level/: Communication, trade-off reasoning, cross-functional impact

**Mastery Roadmap appended to LEARNING_PATH.md:**
- GenAI Engineering: Model architectures, fine-tuning vs RAG
- Agentic AI: Agent frameworks, memory, planning, reasoning
- Distributed Systems: Consensus, state management, eventual consistency
- AI Infrastructure: GPU scheduling, inference optimization, serving patterns
- GPU/CUDA basics: GPU memory, compute, bandwidth
- AI Networking: Distributed tracing, service mesh, load balancing
- Model Serving: vLLM, TensorRT, ONNX, batching strategies
- Architecture Interviews: How to think about systems (scalability, reliability, costs)
- AI Product Thinking: How LLMs change product (UX, evals, monetization)
- Governance & Reliability: Model cards, monitoring, drift, bias
- Economics: Token pricing, model efficiency, cost modeling
- Scaling: From prototype to 1M requests/day

### Success Criteria
- [ ] 10+ system design questions + solutions
- [ ] 5+ coding challenges with explanation
- [ ] Mastery roadmap with 8-week → 6-month learning plans
- [ ] Interview Q&A ranked by difficulty

---

## Phase 10: Polish + Docs Site 🚧

### Scope
Final refinement and public presence.

**Documentation site** (mkdocs-material):
- Builds from `docs/` folder
- Navigation: modules organized by layer
- Search enabled
- Deploy to GitHub Pages (auto via GitHub Actions)

**Diagrams** (Excalidraw + Mermaid):
- Architecture diagrams for each case study
- RAG pipeline flow
- Agent orchestration graphs
- Cost optimization decision trees

**Benchmarks & Examples:**
- Consolidated benchmark results (CSV + graphs)
- Tiny runnable examples (copy-paste friendly)
- Gallery of prompts (public templates)

### Success Criteria
- [ ] mkdocs site builds without errors
- [ ] GitHub Pages live and serving
- [ ] All major modules have visual diagrams
- [ ] Benchmark results published

---

## Quick Checklist: What's Done?

- ✅ P1: Architecture + docs + tooling
- 🚧 P2: Core SDK (in queue)
- 🚧 P3–P10: Domain modules (in queue)

Check [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for implementation details.

---

## Questions?

- **How do I contribute to Phase 2?** See [CONTRIBUTING.md](CONTRIBUTING.md)
- **I want to jump to a specific phase.** Read that phase's README.md; dependencies are clearly marked.
- **What's blocking the next phase?** Check "Blockers" section above.

---

*Last updated: Phase 1 active. Next: Phase 2 entry checklist.*
