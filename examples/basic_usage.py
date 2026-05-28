"""
Basic usage examples for core SDK.

Demonstrates chat, streaming, caching, evaluation, and guardrails.
"""

import asyncio

from core.config import get_settings
from core.eval import faithfulness, judge
from core.guardrails import validate_input, validate_output
from core.llm import chat, embed, router, stream
from core.telemetry import meters


async def example_basic_chat():
    """Example: Basic LLM chat."""
    print("\n=== Example 1: Basic Chat ===")

    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]

    response = await chat(messages, temperature=0.0)

    print(f"Response: {response.text}")
    print(f"Tokens: {response.tokens_in} in, {response.tokens_out} out")
    print(f"Cost: ${response.usd_cost:.6f}")
    print(f"Latency: {response.latency_ms:.0f}ms")
    print(f"Model: {response.model}")


async def example_streaming():
    """Example: Streaming responses."""
    print("\n=== Example 2: Streaming ===")

    messages = [
        {"role": "user", "content": "Count from 1 to 5."}
    ]

    print("Streaming response: ", end="", flush=True)
    async for chunk in stream(messages, temperature=0.0):
        print(chunk.content, end="", flush=True)
    print()


async def example_model_router():
    """Example: Model routing."""
    print("\n=== Example 3: Model Routing ===")

    # Cheap model for classification
    cheap_model = router.choose("classification")
    print(f"Classification task → {cheap_model}")

    # Smart model for reasoning
    smart_model = router.choose("reasoning")
    print(f"Reasoning task → {smart_model}")


async def example_embeddings():
    """Example: Generate embeddings."""
    print("\n=== Example 4: Embeddings ===")

    texts = ["Hello world", "AI engineering", "Production systems"]
    embeddings = await embed(texts)

    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")


async def example_guardrails():
    """Example: Input/output validation."""
    print("\n=== Example 5: Guardrails ===")

    # Test PII detection
    user_input = "My email is john@example.com and SSN is 123-45-6789"
    result = await validate_input(user_input)

    print(f"Input valid: {result.valid}")
    print(f"Message: {result.message}")
    if result.redacted:
        print(f"Redacted: {result.redacted}")

    # Test output validation
    output = "The answer is in [Source: Document 1]"
    result = await validate_output(output, policy="citations_required")
    print(f"Output valid: {result.valid}")


async def example_evaluation():
    """Example: LLM-as-judge evaluation."""
    print("\n=== Example 6: Evaluation ===")

    prediction = "Paris is the capital of France."
    reference = "The capital of France is Paris."
    rubric = "Does the prediction accurately state the same fact as the reference?"

    score = await judge(prediction, reference, rubric)

    print(f"Score: {score.score:.2f}")
    print(f"Reasoning: {score.reasoning}")


async def example_metrics():
    """Example: View telemetry metrics."""
    print("\n=== Example 7: Telemetry Metrics ===")

    stats = meters.get_stats()

    print("Metrics collected:")
    print(f"  Tokens in: {stats['tokens_in']}")
    print(f"  Tokens out: {stats['tokens_out']}")
    print(f"  USD cost: {stats['usd_cost']}")
    print(f"  Cache hits: {stats['cache_hits']}")


async def main():
    """Run all examples."""
    print("="*60)
    print("Core SDK Examples")
    print("="*60)

    settings = get_settings()
    print(f"\nEnvironment: {settings.ENVIRONMENT}")
    print(f"Default LLM: {settings.DEFAULT_LLM}")
    print(f"Caching enabled: {settings.ENABLE_CACHE}")

    # Check API keys
    if not settings.ANTHROPIC_API_KEY and not settings.OPENAI_API_KEY:
        print("\n⚠️  No API keys found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")
        print("Skipping LLM examples...")
        return

    try:
        # Run examples
        await example_basic_chat()
        await example_streaming()
        await example_model_router()
        await example_embeddings()
        await example_guardrails()
        await example_evaluation()
        await example_metrics()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure Redis is running: docker-compose up -d")

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
