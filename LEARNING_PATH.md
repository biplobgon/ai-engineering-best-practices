# Learning Path: 0 → Senior AI Engineer → AI Architect (by 2030)

Navigate your AI engineering mastery in phases. Choose your starting point.

---

## TL;DR: Find Your Path

| Your Role | Start Here | Timeline | Focus |
|---|---|---|---|
| **Junior/Mid** (0–2 yrs AI exp) | Fundamentals → Prompt Eng → RAG | 6–8 months | Core concepts, hands-on |
| **Senior Engineer** (2–5 yrs) | Token/Cost → LLMOps → Deployment → Case Studies | 3–6 months | Production patterns, tradeoffs, architecture |
| **Staff/Architect** (5+ yrs) | System Design → Mastery Roadmap → Interview Prep | 2–4 months | Deep reasoning, communication, strategy |
| **Career Pivot** (from SWE/ML) | Fundamentals → Agents → Multi-Agent | 4–6 months | Agentic patterns, observability, reasoning |

---

## Phase-Based Learning (Junior → Senior)

### Month 1: Fundamentals (Weeks 1–4)

**Goal:** Lock in core mechanics. Understand what's happening under the hood.

**Modules:**
1. `fundamentals/01-llm-basics/` — Tokenization, context, sampling parameters
   - **Learn:** How tokens work; why they cost money
   - **Do:** Token counter; experiment with `temperature`, `top_p`
   - **Time:** 4 hours
   
2. `fundamentals/02-tokens-and-cost/` — Token counting, pricing models
   - **Learn:** Cost calculation; model pricing; ROI
   - **Do:** Build cost calculator; compare models
   - **Time:** 3 hours
   
3. `fundamentals/03-sampling-params/` — Temperature, top_p, frequency/presence penalties
   - **Learn:** How each param affects output; tradeoffs
   - **Do:** Experiment with parameter tuning
   - **Time:** 4 hours
   
4. `fundamentals/04-context-windows/` — Context limits, sliding windows, memory management
   - **Learn:** Why context matters; how to manage it
   - **Do:** Implement context manager; test limits
   - **Time:** 3 hours
   
5. `fundamentals/05-embeddings/` — Dense vectors, similarity, embedding costs
   - **Learn:** How embeddings work; when to use them
   - **Do:** Generate embeddings; compute similarities
   - **Time:** 4 hours

**Week 1 assignments:** Token counter + cost calculator ✅
**Week 2–3 assignments:** Parameter tuning report + embeddings experiment ✅
**Week 4 assignment:** Context management system + cost report 📋

---

### Month 2: Prompt Engineering (Weeks 5–8)

**Goal:** Master prompt design. Write high-quality, efficient prompts.

**Modules:**
1. `prompt-engineering/patterns/` — Zero-shot, few-shot, CoT, ReAct, self-consistency
   - **Learn:** When each pattern excels; cost/quality tradeoffs
   - **Do:** Implement each; benchmark on simple task
   - **Time:** 5 hours
   
2. `prompt-engineering/templates/` — Reusable, versioned prompts
   - **Learn:** Prompt versioning; parameterization
   - **Do:** Build prompt template library (5+ templates)
   - **Time:** 3 hours
   
3. `prompt-engineering/optimization/` — Token reduction, compression, auto-tuning
   - **Learn:** How to write concise prompts; benchmarking
   - **Do:** Optimize a prompt; measure token savings
   - **Time:** 4 hours
   
4. `prompt-engineering/anti-patterns/` — What NOT to do
   - **Learn:** Common mistakes; why they fail
   - **Do:** Identify anti-patterns in examples; refactor
   - **Time:** 2 hours

**Week 5 assignment:** Pattern comparison matrix (CoT vs ReAct vs few-shot) ✅
**Week 6–7 assignment:** Versioned prompt library (5+ templates with evals) ✅
**Week 8 assignment:** Optimization report (tokens saved, cost reduced) 📋

---

### Months 3–4: Optimization (Weeks 9–16)

**Goal:** Build cost/latency/token awareness into every decision.

**Modules:**
1. `cost-optimization/` — Routing, caching, semantic cache, prompt caching
   - **Learn:** Cheap-first architectures; cache ROI
   - **Do:** Build router; implement caching; measure savings
   - **Time:** 6 hours
   
2. `token-optimization/` — Compression, pruning, summarization
   - **Learn:** Context reduction strategies
   - **Do:** Build summarizer; measure quality vs cost tradeoff
   - **Time:** 4 hours
   
3. `latency-optimization/` — Streaming, async batching, parallel execution
   - **Learn:** Throughput vs latency; async patterns
   - **Do:** Stream endpoint; batch embeddings
   - **Time:** 4 hours

**Week 9–10 assignment:** Model router (cheap + fallback) ✅
**Week 11–12 assignment:** Semantic cache integration + benchmark 📋
**Week 13–14 assignment:** Summarization pipeline 📋
**Week 15–16 assignment:** Streaming endpoint + latency report 📋

---

### Months 5–6: RAG (Weeks 17–24)

**Goal:** Master retrieval-augmented generation. Understand retrieval engineering.

**Modules:**
1. `rag/01-naive-rag/` — Embed + retrieve + prompt (the baseline)
   - **Learn:** RAG fundamentals
   - **Do:** Naive RAG on simple corpus
   - **Time:** 3 hours
   
2. `rag/02-chunking-strategies/` — Optimal chunk sizes, overlap, semantic chunks
   - **Learn:** Chunking impact on retrieval quality
   - **Do:** Benchmark chunk sizes; measure tradeoffs
   - **Time:** 4 hours
   
3. `rag/03-hybrid-retrieval/` — BM25 + dense + RRF
   - **Learn:** Why hybrid > dense alone; ensemble value
   - **Do:** Implement hybrid; measure recall improvements
   - **Time:** 5 hours
   
4. `rag/04-rerankers/` — Reranking logic; cost/quality
   - **Learn:** When reranking helps; cost impact
   - **Do:** Add Cohere reranker; benchmark
   - **Time:** 3 hours
   
5. `rag/05-query-rewriting/` — Query expansion, decomposition, rephrasing
   - **Learn:** Query optimization techniques
   - **Do:** Implement query expander
   - **Time:** 3 hours
   
6. `rag/06-graph-rag/` — Knowledge graphs + entity extraction
   - **Learn:** Structured retrieval; graph traversal
   - **Do:** Build simple entity graph
   - **Time:** 4 hours
   
7. `rag/07-agentic-rag/` — RAG agent; decide when to retrieve
   - **Learn:** Agentic retrieval decisions
   - **Do:** RAG agent with retrieval decision loop
   - **Time:** 5 hours
   
8. `rag/08-eval-ragas/` — RAGAS evaluation pipeline
   - **Learn:** Eval metrics; regression gates
   - **Do:** Build eval suite for RAG system
   - **Time:** 4 hours

**Week 17–18 assignment:** Naive RAG + chunking comparison 📋
**Week 19–20 assignment:** Hybrid retrieval + benchmark matrix 📋
**Week 21–22 assignment:** Query rewriting + reranking pipeline 📋
**Week 23–24 assignment:** Complete RAG system with RAGAS evals ✅

---

## Advanced Phase: Senior Engineer (Months 7–9)

### Month 7: Agents & Reasoning (Weeks 25–28)

**Modules:**
1. `agents/react-from-scratch/` — ReAct loop, no framework
2. `agents/tool-calling/` — OpenAI tools API
3. `agents/planning-agents/` — Plan-execute-verify
4. `agents/reflection-agents/` — Self-correction

**Week 25–26 assignment:** ReAct agent from scratch ✅
**Week 27–28 assignment:** Tool-calling system + reflection loop 📋

---

### Month 8: Multi-Agent & Orchestration (Weeks 29–32)

**Modules:**
1. `multi-agent/supervisor-pattern/` — One supervisor, many specialists
2. `multi-agent/debate-pattern/` — Agents argue; human/model decides
3. `orchestration/` — LangGraph state machines

**Week 29–30 assignment:** Supervisor system (3+ agents) ✅
**Week 31–32 assignment:** LangGraph workflow + debate pattern 📋

---

### Month 9: Production & Observability (Weeks 33–36)

**Modules:**
1. `ai-observability/` — OTel tracing, cost metrics
2. `llmops/` — Prompt versioning, A/B testing, drift detection
3. `deployment/` — FastAPI service, async jobs, streaming

**Week 33–34 assignment:** Full observability setup + dashboards 📋
**Week 35–36 assignment:** Production FastAPI service + deployment 📋

---

## Expert Phase: Architect (Months 10–12)

### Month 10: Case Studies (Weeks 37–40)

**Build 3 end-to-end systems:**
1. `enterprise-case-studies/multi-tenant-llm-platform/` — Platform architecture
2. `enterprise-case-studies/agentic-research-assistant/` — Agentic system
3. `enterprise-case-studies/financial-compliance-doc-qa/` — RAG + guardrails

Each includes:
- Full architecture diagram
- Complete code (runnable)
- Cost report
- Eval suite
- Production considerations

---

### Month 11: Interview Prep (Weeks 41–44)

**Modules:**
1. `interview-prep/system-design-questions/` — 10+ questions + walkthroughs
2. `interview-prep/coding-rounds/` — LLM-specific coding challenges
3. `interview-prep/ml-llm-fundamentals/` — Deep dives on key concepts

---

### Month 12: Mastery Roadmap (Weeks 45–48)

**See section below: Senior AI Engineer Mastery Roadmap**

---

## Senior AI Engineer Mastery Roadmap (Deep Expertise)

This section maps the path from **Senior Engineer → Staff/Architect → Principal**.

### 1. GenAI Engineering Fundamentals (Week 1–2)

**Concepts:**
- Transformer architecture (conceptual, not detailed math)
- Attention mechanisms and why they matter
- Token-level understanding at the hardware level
- Model scaling laws (Chinchilla, etc.)
- Fine-tuning vs RAG tradeoffs

**Why it matters:**
- Informs all architecture decisions
- Explains model behavior under stress
- Foundation for staff-level reasoning

**Resources:**
- Read: "Attention Is All You Need" (focus on concepts, not math)
- Video: Andrej Karpathy's "Let's Build GPT" (YouTube)
- Implement: Simple transformer block from scratch

**Interview Q:** "Why does RAG usually beat fine-tuning? When would you fine-tune instead?"

---

### 2. Agentic AI & Reasoning Systems (Week 3–4)

**Concepts:**
- Agent architectures (ReAct, Chain-of-Thought, Tree-of-Thought)
- Multi-turn reasoning and state management
- Tool-use patterns and grounding
- Planning and decomposition strategies
- Long-horizon reasoning challenges

**Why it matters:**
- Agentic AI is the 2025–2026 frontier
- Separates engineers from architects
- Enables solving complex, multi-step problems

**Deep dives:**
- Implement Tree-of-Thought vs ReAct comparison
- Build supervision + handoff patterns
- Explore reflection loops and self-correction

**Interview Q:** "Design a research assistant that can search the web, read papers, and synthesize findings. How do you handle hallucination and citation?"

---

### 3. Distributed Systems & Concurrency (Week 5–6)

**Concepts:**
- Async/await, threads, processes, and when to use each
- Event loops and backpressure
- Eventual consistency and CAP theorem
- Distributed tracing and observability
- Service-oriented architecture patterns

**Why it matters:**
- LLM systems are inherently I/O-bound (waiting on API calls)
- Architect must design for 1M concurrent users
- Debugging distributed systems requires deep knowledge

**Deep dives:**
- Load testing with concurrent LLM calls
- Implement circuit breakers and fallback strategies
- Design rate limiting + token bucket algorithms
- Trace propagation across services

**Interview Q:** "Design an LLM API service for 1M concurrent users. How do you handle rate limits, fallbacks, and observability?"

---

### 4. AI Infrastructure & GPU Systems (Week 7–8)

**Concepts:**
- GPU memory model (VRAM, shared memory, L1/L2 cache)
- CUDA basics (kernels, threads, blocks, warps)
- Model parallelism vs data parallelism
- Quantization and inference optimization
- Batching strategies for throughput
- vLLM, TensorRT, ONNX
- Operator fusion and kernel optimization

**Why it matters:**
- Inference cost is the #1 blocker for AI companies
- Staff engineers optimize 10–100× cost/latency improvements
- GPU-aware design unlocks 10× better performance

**Deep dives:**
- Profile a model with nsys/nvprof
- Implement batch inference with vLLM
- Quantize a model (INT8, FP8, etc.)
- Measure impact on latency and accuracy

**Interview Q:** "You're deploying Llama 2 70B on AWS. Design the inference stack for cost and latency. What are your bottlenecks?"

---

### 5. AI Networking & Distributed Inference (Week 9–10)

**Concepts:**
- Request batching across machines
- All-reduce collectives for distributed training
- Tensor parallelism communication patterns
- Low-latency networking (RDMA, InfiniBand concepts)
- Service mesh patterns (Istio, etc.)
- Load balancing strategies for inference

**Why it matters:**
- Scaling beyond one machine requires distributed systems thinking
- Communication is often the bottleneck
- Staff engineers design for 10–100K tokens/sec throughput

**Deep dives:**
- Implement distributed embedding batching
- Design a batch scheduler for multiple GPUs
- Analyze communication overhead in tensor parallel models
- Set up observability for distributed tracing

**Interview Q:** "Design a service that runs inference on 100 GPUs. How do you schedule batches, minimize communication, and handle failures?"

---

### 6. Model Serving & Production Inference (Week 11–12)

**Concepts:**
- vLLM, TensorRT-LLM, DeepSpeed-Inference
- Batch scheduling and continuous batching
- KV-cache management
- Speculation and token prediction
- Model caching and warm pools
- Blue-green deployments
- Canary releases for models

**Why it matters:**
- Inference is where the cost lives (80% of operational expense)
- Every 1% latency improvement = 1% cost improvement
- Architects design for reliability + cost simultaneously

**Deep dives:**
- Deploy vLLM on Kubernetes
- Implement token streaming with continuous batching
- Design autoscaling for variable load
- Compare throughput: batch size, prefill vs decode costs

**Interview Q:** "Your LLM API is experiencing 10s latency at peak. Diagnose the bottleneck (prefill? memory? I/O?) and propose solutions."

---

### 7. Architecture & System Design Patterns (Week 13–14)

**Concepts:**
- CQRS (Command Query Responsibility Segregation) for AI systems
- Saga pattern for multi-step workflows
- Event sourcing for audit trails
- Circuit breaker, retry, bulkhead patterns
- Strangler pattern for migrations
- Fan-out, fan-in patterns for parallelism

**Why it matters:**
- Separates senior engineers from architects
- Enables reasoning about trade-offs at scale
- Documented patterns prevent reinventing wheels

**Deep dives:**
- Design a multi-tenant LLM platform with CQRS
- Implement saga pattern for document ingestion → chunking → embedding → indexing
- Event sourcing for audit logs (compliance requirement)
- Failure scenarios: partial failures, cascading failures, recovery

**Interview Q:** "Design a multi-tenant document QA system for 1000 customers. Requirements: isolation, compliance audit trail, cost per customer. What patterns apply?"

---

### 8. AI Observability & Monitoring (Week 15–16)

**Concepts:**
- Distributed tracing (OpenTelemetry, Jaeger)
- Metrics (Prometheus, time-series)
- Logs (structured logging, correlation IDs)
- Golden signals (latency, traffic, errors, saturation)
- Model monitoring (drift, data quality, inference failures)
- SLIs, SLOs, error budgets

**Why it matters:**
- Observability is how you sleep at night
- Architects must design for debuggability at scale
- Blind systems fail silently (costly)

**Deep dives:**
- Instrument end-to-end trace for an LLM request
- Design SLO for LLM API (e.g., p99 latency < 500ms, 99.9% uptime)
- Implement custom metrics (tokens/sec, cost/request, cache hit rate)
- Build dashboards for on-call engineers

**Interview Q:** "An LLM API is meeting latency SLOs but users report poor quality. How do you monitor and debug this?"

---

### 9. AI Product & Business Strategy (Week 17–18)

**Concepts:**
- How LLMs change product UX (streaming, long-context, quality tradeoffs)
- Token economics and pricing strategies
- CAC (cost-to-acquire customer) vs inference cost
- LLM ROI modeling
- When to self-host vs use API
- Competitive positioning (speed, cost, quality, safety)

**Why it matters:**
- Staff engineers think end-to-end, not just code
- Understand business implications of technical choices
- Communicate value to non-technical stakeholders

**Deep dives:**
- Cost model for a subscription LLM product
- ROI analysis: fine-tuning vs RAG vs custom model
- Pricing strategy for pay-per-token vs flat-rate
- Churn analysis: how does inference cost affect revenue?

**Interview Q:** "Your LLM app is spending 40% of revenue on API calls. The business wants profitability. What are 3 approaches? Trade-offs?"

---

### 10. AI Governance, Safety & Reliability (Week 19–20)

**Concepts:**
- Alignment and RLHF (conceptual, not implementation)
- Hallucination mitigation (RAG, retrieval validation)
- Prompt injection and adversarial examples
- Model cards and ethical guidelines
- OWASP LLM Top 10
- Red-teaming and evaluation
- PII and data privacy in LLM systems
- Audit trails and compliance

**Why it matters:**
- LLMs are probabilistic; failures are asymmetric
- Regulatory requirements (GDPR, CCPA, etc.) tighten
- Reputational damage from hallucinations/bias is severe
- Staff engineers design for reliability + safety simultaneously

**Deep dives:**
- Implement guardrails (input validation, output checking)
- Design red-teaming process
- Build audit trail (who asked what, what was returned, when)
- Compliance checklist for regulated industries

**Interview Q:** "Design an LLM system for a bank. Constraints: hallucinations unacceptable, audit trail required, PII detection. How?"

---

### 11. AI Economics & Scaling (Week 21–22)

**Concepts:**
- Token pricing and cost reduction strategies
- Economies of scale in inference
- Batch processing cost vs latency
- Caching ROI (semantic + prompt caching)
- Model selection and cost/quality tradeoffs
- Infrastructure costs (GPU, networking, storage)
- Profitability analysis for LLM businesses

**Why it matters:**
- LLM costs are the primary blocker at scale
- 1% cost improvement = 1% profit improvement
- Architects balance cost + quality + latency

**Deep dives:**
- Build cost model for 1M users
- Cost comparison: API vs self-hosted vs hybrid
- Analyze break-even for different use cases
- Design cost optimization roadmap

**Interview Q:** "Your LLM product costs $0.10 to serve per user. Revenue is $0.15/user. Scale to 10M users profitably."

---

### 12. Reasoning Under Uncertainty & Trade-offs (Week 23–24)

**Concepts:**
- Decision-making with incomplete information
- Technical vs business trade-offs
- Risk assessment (performance, cost, reliability)
- Architectural alternatives (monolith vs micro vs serverless)
- Migration strategies
- When to build vs buy

**Why it matters:**
- Real-world problems don't have optimal solutions
- Architects must communicate reasoning clearly
- Trade-offs are where staff-level thinking shows

**Deep dives:**
- 5 architectural options for RAG system; pros/cons each
- Migration plan: monolith → microservices
- When to use external APIs vs self-hosted
- Risk assessment: what goes wrong? how do you recover?

**Interview Q:** "Design a ChatGPT competitor from scratch. What are the 3 biggest architectural decisions? Justify each."

---

## Learning Resource Index

| Topic | Recommended | Format | Time |
|---|---|---|---|
| Transformers | Karpathy "Let's Build GPT" | Video | 3 hrs |
| Agents | Original ReAct paper | Paper | 1 hr |
| vLLM | vLLM documentation + GitHub | Docs + Code | 4 hrs |
| CUDA | Nvidia CUDA C Programming Guide | Docs | 8 hrs |
| Distributed Systems | "Designing Data-Intensive Applications" | Book | 20 hrs |
| Kubernetes | Kubernetes documentation | Docs | 4 hrs |
| OpenTelemetry | OTel documentation + examples | Docs + Code | 3 hrs |

---

## Checkpoints: Track Your Progress

- **Month 1-2:** Fundamentals locked ✅
- **Month 3-4:** Optimization mastered ✅
- **Month 5-6:** RAG fully implemented ✅
- **Month 7-9:** Agents + production experience ✅
- **Month 10-12:** Architect-level thinking + interview prep ✅

**Total timeline:** 12 months from mid-level engineer → Staff AI Engineer

---

## Next Steps

1. **Choose your starting point** above
2. **Follow the week-by-week path**
3. **Do the assignments** (code, benchmarks, reports)
4. **Review case studies** to see patterns in action
5. **Prep for interviews** in Month 11 (system design Q&A)
6. **Build portfolio projects** as you go — they speak louder than resume

---

## Questions?

See [README.md](README.md) for module overview or [CONTRIBUTING.md](CONTRIBUTING.md) for how to add content.

---

*Last updated: Phase 1. Curriculum expanded in Phase 3–9.*
