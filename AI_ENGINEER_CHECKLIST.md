# AI Engineer Production Readiness Checklist

Use this checklist to ensure your AI system is production-ready. It covers quality, observability, cost, and reliability.

---

## Pre-Launch (Before first user)

### Code Quality
- [ ] All public functions have type hints
- [ ] All public functions have docstrings (Google-style)
- [ ] `ruff check .` passes (no import boundary violations)
- [ ] `black --check .` passes
- [ ] `mypy core/` passes
- [ ] Test coverage > 80% for core modules
- [ ] All tests pass: `pytest -v tests/ core/`

### Testing
- [ ] Unit tests for all major functions
- [ ] Integration tests with real Redis + Postgres
- [ ] Eval suite runs and passes
- [ ] Load test (concurrent requests): latency p99 < target
- [ ] Error scenarios tested (API timeout, rate limit, invalid input)

### Observability
- [ ] Every LLM call emits OTel span
- [ ] Spans include: `tokens_in`, `tokens_out`, `usd_cost`, `latency_ms`, `model`, `cached`
- [ ] Structured logging (JSON, correlation IDs)
- [ ] Metrics scraped by Prometheus (or equivalent)
- [ ] Dashboard built (Grafana or equivalent)
- [ ] Alert rules defined (latency > threshold, error rate, cost anomaly)

### Cost & Performance
- [ ] Cost per operation calculated and logged
- [ ] Token usage tracked per feature
- [ ] Cache hit rate monitored
- [ ] Latency p50, p99 measured and within SLO
- [ ] Model routing strategy documented
- [ ] Inference cost model built ($/1M users)

### Security & Governance
- [ ] API keys in `.env` (not committed)
- [ ] PII detection in place (input validation)
- [ ] Output validation checks hallucinations + citations
- [ ] Rate limiting per user/API key
- [ ] Audit log captures: who, what, when, result
- [ ] OWASP LLM Top 10 checklist completed
- [ ] Data retention policy documented

### Documentation
- [ ] Architecture diagram (system, data flow, components)
- [ ] README with quick start
- [ ] API documentation (endpoints, examples, error codes)
- [ ] Deployment guide (steps to deploy to prod)
- [ ] Runbook for on-call engineer (common issues + fixes)
- [ ] Trade-off document (speed vs cost vs quality decisions)
- [ ] Cost report (baseline + projected 1M user cost)

---

## Launch Day (Canary / limited release)

### Deployment
- [ ] Code deployed to staging; all tests pass
- [ ] Configuration validated (env vars, secrets)
- [ ] Canary traffic < 10% of users (if possible)
- [ ] Rollback plan documented and tested
- [ ] Database backups scheduled
- [ ] Logs centralized (Cloudwatch, Datadog, etc.)

### Monitoring (Go/No-Go Decision)
- [ ] Latency p99 < SLO
- [ ] Error rate < 0.1%
- [ ] Cost per request as expected
- [ ] Cache hit rate > expected baseline
- [ ] Token usage per request < budget
- [ ] Zero critical alerts firing
- [ ] Escalation path (on-call person) set up

### Team Readiness
- [ ] On-call rotation established
- [ ] Incident response plan documented
- [ ] Escalation procedures clear
- [ ] Comms plan for outages (status page, Slack, etc.)
- [ ] Team trained on monitoring + debugging

---

## Week 1–4 Post-Launch

### Reliability
- [ ] Zero unplanned downtime
- [ ] All alerts firing appropriately (no false positives)
- [ ] Graceful degradation tested (API fail → fallback)
- [ ] Circuit breaker tripped; recovery works
- [ ] Rate limiting under load
- [ ] Database latency < 100ms p99

### Cost Tracking
- [ ] Daily cost reports reviewed
- [ ] Token usage per user/feature tracked
- [ ] No runaway costs (e.g., due to inefficient retrieval)
- [ ] ROI of caching validated (savings > 50%)
- [ ] Model routing working (cheap model used 80%+ of time)

### Quality
- [ ] Eval metrics stable
- [ ] No degradation in hallucination rate
- [ ] Citation accuracy > 95% (if applicable)
- [ ] User feedback positive (if collecting)
- [ ] Latency acceptable to users

### Observability
- [ ] Dashboards showing: latency, error rate, cost, cache hit, token usage
- [ ] Alerts tuned (no alert fatigue)
- [ ] Logs searchable and useful for debugging
- [ ] Trace sampling rate set (100% at first, reduce later if cost/perf issue)

---

## Month 1–3 (Stabilization & Optimization)

### Performance
- [ ] Latency optimized (streaming if applicable)
- [ ] Batch processing implemented (where parallelism helps)
- [ ] Cache hit rate analyzed and optimized
- [ ] Model routing working optimally (fallback rate < 5%)
- [ ] Database indexes optimized

### Cost
- [ ] Semantic cache deployed and working
- [ ] Prompt caching enabled (if supported by provider)
- [ ] Prompt optimization complete (shorter while maintaining quality)
- [ ] Token usage reduced by 10%+ from launch
- [ ] ROI of each cost optimization measured

### Reliability
- [ ] SLOs met consistently (99.9% uptime, p99 latency)
- [ ] Incidents resolved within SLA
- [ ] Root cause analysis done for any incident
- [ ] Preventive measures implemented
- [ ] Disaster recovery tested (can restore data in <1 hr)

### Governance
- [ ] Compliance requirements validated
- [ ] Data retention policy enforced
- [ ] Audit trail complete and immutable
- [ ] PII handling verified
- [ ] Security review passed (pen test if applicable)

---

## Ongoing (Monthly Cadence)

### Health Checks
- [ ] Cost trending analysis (increasing? why?)
- [ ] Quality metrics stable
- [ ] User satisfaction scores reviewed
- [ ] Performance benchmarks run
- [ ] Security patches applied promptly

### Optimization
- [ ] New prompts A/B tested before rollout
- [ ] Models upgraded when available (if cost/quality improves)
- [ ] Retrieval strategy benchmarked quarterly
- [ ] Infrastructure scaling reviewed (horizontally or vertically)
- [ ] Unused features / dead code removed

### Team
- [ ] On-call handoff smooth
- [ ] Runbooks up-to-date
- [ ] Knowledge transfer happening (no bus factor)
- [ ] Incident post-mortems completed
- [ ] Team professional development ongoing

---

## Scaling to Production (10M+ users / 100M calls/month)

### Architecture
- [ ] Multi-region deployment (if needed)
- [ ] Database replication + failover working
- [ ] Load balancing across services
- [ ] Cache sharding / Redis Cluster
- [ ] Queue system (Celery/RQ) for async jobs
- [ ] Graceful degradation at traffic spikes

### Cost at Scale
- [ ] Inference costs < 50% of revenue (sustainable margin)
- [ ] Batch processing used where applicable
- [ ] Model routing still prioritizing cheap models
- [ ] Caching yielding 70%+ savings on repeated queries

### Reliability
- [ ] 99.99% uptime SLO (4 nines)
- [ ] P99 latency < 500ms even at peak
- [ ] Error rate < 0.01%
- [ ] Incident MTTR < 5 minutes

### Observability
- [ ] Distributed tracing on every request
- [ ] Real-time alerts for anomalies (cost spikes, latency shifts)
- [ ] Custom dashboards for each team (eng, product, finance)
- [ ] Trace sampling optimized (not 100%, but enough signal)

---

## Interview Prep: Articulate Your System

When interviewing (for senior/architect roles), be ready to discuss:

1. **Architecture:** What are the main components? How do they interact?
2. **Trade-offs:** Why this design? What alternatives did you consider?
3. **Scale:** How does it scale to 10M users? Where are bottlenecks?
4. **Cost:** How much does it cost to run? How did you optimize?
5. **Reliability:** How do you handle failures? What's your uptime?
6. **Observability:** How do you know if something's wrong?
7. **Debugging:** Walk through: user reports latency issue, you investigate.

---

## Self-Assessment: Are You Ready?

Answer honestly:

- [ ] I can explain my system's architecture in 10 minutes
- [ ] I understand every critical component (no black boxes)
- [ ] I've load-tested it and know the limits
- [ ] I can articulate cost per user and ROI
- [ ] I've debugged a production incident end-to-end
- [ ] I have monitoring + alerts set up
- [ ] I know how to roll back if something breaks
- [ ] I can scale this to 10× current traffic
- [ ] I've done cost optimization analysis
- [ ] I've designed for failure modes (graceful degradation)

**Score:** 8+ → Ready for production ✅ | 6–7 → Almost there, tighten a few things | < 6 → Not yet, more work needed

---

## Next Steps

- **Just launched?** Focus on reliability + observability (Month 1–3 section)
- **Scaling?** Focus on cost + architecture (Scaling section)
- **Interviewing soon?** Practice articulating your system with others

---

*Use this checklist to ship with confidence and sleep at night.*
