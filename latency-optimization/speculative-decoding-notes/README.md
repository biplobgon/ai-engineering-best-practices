# Speculative Decoding

**Status:** Conceptual overview (implementation requires special model support)

---

## Overview

Speculative decoding is an advanced technique that can achieve 2-3x speedup in LLM inference by using a small "draft" model to predict tokens in parallel with verification by a larger "target" model.

**Important:** This is not something you can implement at the API level. It requires:
- Access to model internals (logits, hidden states)
- Self-hosted models
- Specialized inference engines

This guide explains the concept for educational purposes.

---

## How It Works

### Standard Autoregressive Decoding

```
Token 1: [Wait 100ms] → "The"
Token 2: [Wait 100ms] → "cat"
Token 3: [Wait 100ms] → "sat"
Total: 300ms for 3 tokens
```

Each token must wait for the previous token to complete.

### Speculative Decoding

```
Draft model (fast, small):
  Predicts 5 tokens in parallel: "The cat sat on the"
  Time: 50ms

Target model (slow, large):
  Verifies all 5 tokens in parallel: ✓ ✓ ✓ ✗ ✗
  Time: 150ms
  
Result: 3 correct tokens in 200ms (vs 300ms sequential)
Speedup: 1.5x for this example
```

---

## Key Concepts

### 1. Draft Model

- Small, fast model (e.g., 1B parameters)
- Generates k candidate tokens
- Low quality, but fast
- Examples: TinyLLaMA, SmolLM, Phi-2

### 2. Target Model

- Large, accurate model (e.g., 70B parameters)
- Verifies all k candidates in parallel
- High quality
- Examples: Llama-3-70B, Mistral-Large

### 3. Verification

Target model checks draft predictions:
- ✓ If draft token matches target distribution → Accept
- ✗ If draft token is wrong → Reject and regenerate from that point

---

## Theoretical Speedup

### Best case: All predictions correct
```
Sequential: k tokens × t_target = k×t
Speculative: t_draft + t_target = constant
Speedup: k × (t_target / (t_draft + t_target))
```

For k=5, t_target=100ms, t_draft=20ms:
- Sequential: 500ms
- Speculative: 120ms
- **Speedup: 4.2x**

### Average case: 60% acceptance rate
```
Effective speedup: ~2-3x
```

---

## Requirements

### Infrastructure
- Self-hosted models (cannot use OpenAI/Anthropic APIs)
- GPU with enough VRAM for both models
- Specialized inference engine:
  - vLLM (supports speculative decoding)
  - TensorRT-LLM
  - ExLlamaV2
  - SGLang

### Model Compatibility
- Draft and target must use same tokenizer
- Draft should be distilled version of target (or similar architecture)
- Common pairs:
  - Llama-3-8B (draft) + Llama-3-70B (target)
  - Mistral-7B (draft) + Mixtral-8x22B (target)

---

## Implementation Sketch

### With vLLM

```python
from vllm import LLM, SamplingParams

# Initialize with draft model
llm = LLM(
    model="meta-llama/Llama-3-70b",
    speculative_model="meta-llama/Llama-3-8b",  # Draft model
    num_speculative_tokens=5,  # k candidates
)

# Generate with speculative decoding
outputs = llm.generate(prompts, sampling_params)
# Automatically uses speculative decoding
```

### With SGLang

```python
import sglang as sgl

# Load target and draft models
target = sgl.Engine(model="Llama-3-70b")
draft = sgl.Engine(model="Llama-3-8b")

# Enable speculative decoding
with sgl.speculative_decode(target=target, draft=draft, k=5):
    output = target.generate(prompt)
```

---

## When to Use

### ✅ Good fit:
- High-volume inference (cost matters)
- Self-hosted models
- Latency-critical applications
- Long-form generation (more tokens = more savings)

### ❌ Not suitable:
- API-based models (OpenAI, Anthropic)
- Low-volume applications (setup overhead)
- Very short outputs (<10 tokens)
- Memory-constrained environments

---

## Alternatives at API Level

Since speculative decoding isn't available via APIs, consider:

### 1. Streaming (this repo)
- Immediate perceived latency improvement
- Available for all API providers
- See: [`latency-optimization/streaming/`](../streaming/)

### 2. Parallel tool calls (this repo)
- Run independent operations concurrently
- 3-5x speedup for multi-step workflows
- See: [`latency-optimization/parallel-tool-calls/`](../parallel-tool-calls/)

### 3. Model routing
- Route simple queries to fast models
- Use slow models only when needed
- See: [`core/llm/router.py`](../../core/llm/router.py)

### 4. Prompt compression
- Reduce input tokens → faster processing
- See: [`token-optimization/`](../../token-optimization/)

---

## Research & Further Reading

### Key Papers

1. **"Fast Inference from Transformers via Speculative Decoding"**
   - Chen et al., 2023
   - Original speculative decoding paper
   - https://arxiv.org/abs/2211.17192

2. **"SpecInfer: Accelerating Generative LLM Serving with Speculative Inference"**
   - Miao et al., 2024
   - Production system at Meta
   - https://arxiv.org/abs/2305.09781

3. **"Medusa: Simple LLM Inference Acceleration with Multiple Decoding Heads"**
   - Cai et al., 2024
   - Alternative approach using multiple heads
   - https://arxiv.org/abs/2401.10774

### Blog Posts & Tutorials

- **vLLM Documentation:** https://docs.vllm.ai/en/latest/
- **HuggingFace: Speculative Decoding Guide**
- **Anyscale: Ray Serve with Speculative Decoding**

### Open Source Tools

- **vLLM:** https://github.com/vllm-project/vllm
- **SGLang:** https://github.com/sgl-project/sglang
- **TensorRT-LLM:** https://github.com/NVIDIA/TensorRT-LLM
- **ExLlamaV2:** https://github.com/turboderp/exllamav2

---

## Summary

**Speculative decoding is powerful but requires self-hosted infrastructure.**

For API-based applications (OpenAI, Anthropic, etc.):
1. Use streaming for perceived latency (this module)
2. Use parallel execution for real latency (this module)
3. Use prompt compression to reduce tokens (token-optimization module)

For self-hosted applications:
1. Evaluate if 2-3x speedup justifies complexity
2. Ensure you have compatible draft/target models
3. Use vLLM or SGLang for production deployment

---

*Created in Phase 3. Educational content only - implementation requires self-hosted models.*
