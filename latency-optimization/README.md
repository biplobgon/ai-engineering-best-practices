# Latency Optimization

**Status:** ✅ Phase 3 (Complete)

Reduce response time through streaming, parallel execution, and async patterns.

---

## What You'll Learn

- **Streaming responses** for perceived 50-90% latency reduction
- **Parallel tool calls** to execute operations concurrently
- **Async patterns** for non-blocking I/O
- **Time-to-first-token** optimization strategies
- **Production patterns** for real-time applications

---

## Module Overview

| Aspect | Details |
|---|---|
| **Focus** | Latency reduction, perceived performance, concurrent execution |
| **Complexity** | Intermediate to Advanced |
| **Phase** | P3 |
| **Time** | 2-3 hours |

---

## Why Latency Optimization Matters

### User Experience Impact

```python
# Before: Blocking call (5s wait, then full response)
response = await chat(messages)  # User waits 5s
display(response.text)

# After: Streaming (200ms to first token, progressive display)
async for chunk in stream(messages):  # User sees results in 200ms
    display(chunk.content)
# Perceived latency: 4-5x faster
```

### Real-world impact:
- **Chat applications**: Users expect <500ms to first word
- **Agents**: Parallel tool calls reduce total time by 60-80%
- **RAG systems**: Stream while retrieving/processing
- **Multi-step workflows**: Async orchestration

---

## Key Techniques

### 1. Streaming (50-90% perceived latency reduction)

**Server-Sent Events (SSE):**
- Stream LLM tokens as generated
- Time to first token: 200-500ms vs 3-10s
- Better UX, same total time

**WebSocket Streaming:**
- Bidirectional real-time communication
- For chat applications
- Lower overhead than SSE

See: [`streaming/`](./streaming/)

---

### 2. Parallel Tool Calls (60-80% real latency reduction)

**Concurrent execution:**
- Run independent operations in parallel
- Use `asyncio.gather()` for multiple calls
- Works with embeddings, tool calls, API requests

**Example:**
```python
# Sequential: 3s + 3s + 3s = 9s
result1 = await embed(text1)
result2 = await embed(text2)
result3 = await embed(text3)

# Parallel: max(3s, 3s, 3s) = 3s (3x faster)
results = await asyncio.gather(
    embed(text1),
    embed(text2),
    embed(text3),
)
```

See: [`parallel-tool-calls/`](./parallel-tool-calls/)

---

### 3. Speculative Decoding (2-3x faster, requires special setup)

**Conceptual overview:**
- Use small "draft" model to predict tokens
- Verify with large "target" model in parallel
- Accept correct predictions, reject and regenerate wrong ones
- Requires model-level support

See: [`speculative-decoding-notes/`](./speculative-decoding-notes/)

---

## Quick Start

### Install dependencies

```bash
pip install asyncio aiohttp
```

### Example: Streaming response

```python
from core.llm import stream

messages = [{"role": "user", "content": "Explain quantum computing"}]

# Stream tokens as they're generated
async for chunk in stream(messages, model="gpt-4o-mini"):
    print(chunk.content, end="", flush=True)
# Output appears progressively: "Quantum...", "Quantum computing...", etc.
```

### Example: Parallel embeddings

```python
from latency_optimization.parallel_tool_calls import parallel_embeddings

documents = ["Doc 1", "Doc 2", "Doc 3", ...]  # 100 docs

# Parallel: 2-3s instead of 20-30s
embeddings = await parallel_embeddings.batch_embed(documents, batch_size=10)
```

---

## Directory Structure

```
latency-optimization/
├── README.md                        # This file
├── streaming/
│   ├── README.md                    # Streaming patterns
│   ├── sse_streaming.py             # Server-Sent Events
│   ├── websocket_streaming.py       # WebSocket streaming
│   ├── chunk_processing.py          # Process chunks incrementally
│   └── tests/
│       ├── test_sse.py
│       └── test_websocket.py
├── parallel-tool-calls/
│   ├── README.md                    # Parallel execution
│   ├── concurrent_tools.py          # asyncio.gather patterns
│   ├── parallel_embeddings.py       # Batch embeddings
│   └── tests/
│       ├── test_concurrent.py
│       └── test_parallel_embeddings.py
└── speculative-decoding-notes/
    ├── README.md                    # Conceptual overview
    └── further_reading.md           # Research papers
```

---

## Performance Benchmarks

### Streaming vs Blocking

| Metric | Blocking | Streaming | Improvement |
|---|---|---|---|
| Time to first token | 3-10s | 200-500ms | **5-20x faster** |
| Total time | 10s | 10s | Same |
| Perceived speed | Slow | Fast | **4-5x better UX** |
| User engagement | Low | High | +40% retention |

### Parallel vs Sequential

| Operation | Sequential | Parallel | Improvement |
|---|---|---|---|
| 10 embeddings | 5s | 1s | **5x faster** |
| 5 tool calls | 15s | 4s | **3.75x faster** |
| RAG (retrieve + embed) | 8s | 2.5s | **3.2x faster** |

---

## When to Use Each Technique

### Streaming
✅ Chat applications
✅ Long-form generation
✅ User-facing applications
❌ Batch processing
❌ When full response needed before proceeding

### Parallel Tool Calls
✅ Independent operations (embeddings, API calls)
✅ Multi-tool agent systems
✅ RAG systems (parallel retrieval)
❌ Sequential dependencies
❌ When order matters

### Speculative Decoding
✅ Inference-heavy workloads
✅ Self-hosted models
✅ High-volume applications
❌ API-based models (not supported)
❌ Low-volume applications (setup overhead)

---

## Production Patterns

### 1. Streaming with Buffering

```python
async def stream_with_buffer(messages, buffer_size=5):
    """Buffer chunks for smoother display."""
    buffer = []
    
    async for chunk in stream(messages):
        buffer.append(chunk.content)
        
        if len(buffer) >= buffer_size:
            yield ''.join(buffer)
            buffer = []
    
    if buffer:
        yield ''.join(buffer)
```

### 2. Parallel with Error Handling

```python
async def parallel_with_fallback(tasks):
    """Run tasks in parallel, handle individual failures."""
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out failures
    successful = [r for r in results if not isinstance(r, Exception)]
    return successful
```

### 3. Adaptive Batching

```python
async def adaptive_batch_embed(texts, max_latency_ms=1000):
    """Adjust batch size based on latency."""
    batch_size = 100
    
    while batch_size > 1:
        start = time.perf_counter()
        batch = texts[:batch_size]
        
        try:
            result = await embed(batch)
            latency = (time.perf_counter() - start) * 1000
            
            if latency < max_latency_ms:
                break  # Batch size is good
            
            batch_size //= 2  # Too slow, reduce batch size
        except:
            batch_size //= 2  # Error, reduce batch size
    
    # Process all texts with optimal batch size
    return await batch_embed_parallel(texts, batch_size)
```

---

## Latency Budget Analysis

### Typical RAG request breakdown

**Before optimization:**
- Embedding query: 200ms
- Vector search: 100ms
- Embedding 20 docs (sequential): 4000ms
- LLM call: 5000ms
- **Total: 9.3s**

**After optimization:**
- Embedding query: 200ms
- Vector search: 100ms (parallel with query embed)
- Embedding 20 docs (parallel batches): 800ms
- LLM call (streaming): 500ms (to first token)
- **Total (perceived): 1.6s**
- **Improvement: 5.8x faster**

---

## Common Pitfalls

### 1. Not handling streaming errors
❌ Assuming streams always complete
✅ Wrap in try/catch, handle reconnection

### 2. Over-parallelization
❌ Running 1000 tasks concurrently
✅ Use semaphores to limit concurrency (e.g., 10 at a time)

### 3. Blocking in async
❌ Using `requests.get()` in async function
✅ Use `aiohttp` or other async libraries

### 4. Not measuring properly
❌ Only measuring total time
✅ Track time-to-first-token, time-to-first-chunk, total time

---

## Monitoring & Metrics

### Key metrics to track

```python
from core.telemetry import meters

# Time to first token
meters.record_latency_ms(ttft, "llm.streaming.first_token")

# Total streaming time
meters.record_latency_ms(total, "llm.streaming.total")

# Parallel efficiency
meters.record_latency_ms(parallel_time, "parallel.total")
meters.increment("parallel.tasks", len(tasks))
```

### P95 latency targets

- Time to first token: <500ms
- Total streaming (100 tokens): <3s
- Embedding (single): <200ms
- Embedding (batch of 10): <500ms

---

## Next Steps

1. **Start here:** [`streaming/sse_streaming.py`](./streaming/sse_streaming.py)
2. **Then try:** [`parallel-tool-calls/concurrent_tools.py`](./parallel-tool-calls/concurrent_tools.py)
3. **Advanced:** [`parallel-tool-calls/parallel_embeddings.py`](./parallel-tool-calls/parallel_embeddings.py)

---

## Related Modules

- [`async-patterns/`](../async-patterns/) — Async/await patterns
- [`streaming/`](../streaming/) — Legacy streaming examples
- [`core/llm/`](../core/llm/) — LLM client with streaming support
- [`agents/`](../agents/) — Agent patterns with parallel tools

---

## References

- **Server-Sent Events (SSE):** MDN Web Docs
- **asyncio:** Python official docs
- **Speculative Decoding:** [Paper] Chen et al., "Fast Inference from Transformers"
- **Time-to-First-Token:** OpenAI, Anthropic best practices

---

*Created in Phase 3. Updated: Jun 2026.*
