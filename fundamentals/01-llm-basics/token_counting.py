"""
Token Counting: Practical token counting for cost control and context management.

This script demonstrates:
1. Counting tokens before API calls
2. Enforcing budget limits
3. Checking context window limits
4. Estimating latency from token count

Run: python token_counting.py
"""

import tiktoken
from typing import Optional
from dataclasses import dataclass


@dataclass
class TokenBudget:
    """Token budget configuration."""
    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens: int
    price_per_1m_input: float
    price_per_1m_output: float


@dataclass
class TokenCount:
    """Token count result."""
    count: int
    within_budget: bool
    estimated_cost_usd: float
    estimated_latency_sec: float


# Model configurations
MODEL_CONFIGS = {
    "gpt-4": TokenBudget(
        max_input_tokens=128_000,
        max_output_tokens=4_096,
        max_total_tokens=128_000,
        price_per_1m_input=30.0,
        price_per_1m_output=60.0,
    ),
    "gpt-3.5-turbo": TokenBudget(
        max_input_tokens=16_000,
        max_output_tokens=4_096,
        max_total_tokens=16_000,
        price_per_1m_input=0.50,
        price_per_1m_output=1.50,
    ),
    "claude-haiku": TokenBudget(
        max_input_tokens=200_000,
        max_output_tokens=4_096,
        max_total_tokens=200_000,
        price_per_1m_input=0.80,
        price_per_1m_output=4.00,
    ),
}


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens for a given model."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base (GPT-4 encoding)
        enc = tiktoken.get_encoding("cl100k_base")
    
    return len(enc.encode(text))


def check_token_budget(
    text: str,
    model: str = "gpt-4",
    expected_output_tokens: int = 500,
) -> TokenCount:
    """
    Check if text fits within token budget.
    
    Args:
        text: Input text to check
        model: Model name
        expected_output_tokens: Expected response length
        
    Returns:
        TokenCount with budget check results
    """
    config = MODEL_CONFIGS.get(model)
    if not config:
        raise ValueError(f"Unknown model: {model}")
    
    input_tokens = count_tokens(text, model)
    total_tokens = input_tokens + expected_output_tokens
    
    # Check budget
    within_budget = (
        input_tokens <= config.max_input_tokens
        and expected_output_tokens <= config.max_output_tokens
        and total_tokens <= config.max_total_tokens
    )
    
    # Estimate cost
    input_cost = (input_tokens / 1_000_000) * config.price_per_1m_input
    output_cost = (expected_output_tokens / 1_000_000) * config.price_per_1m_output
    estimated_cost = input_cost + output_cost
    
    # Estimate latency (assuming 50 tokens/sec for output)
    estimated_latency = expected_output_tokens / 50.0
    
    return TokenCount(
        count=input_tokens,
        within_budget=within_budget,
        estimated_cost_usd=estimated_cost,
        estimated_latency_sec=estimated_latency,
    )


def validate_request(
    text: str,
    model: str,
    max_cost_usd: float = 0.01,
    max_latency_sec: float = 10.0,
) -> tuple[bool, str]:
    """
    Validate request against budget and latency constraints.
    
    Returns:
        (valid, message) tuple
    """
    result = check_token_budget(text, model)
    
    if not result.within_budget:
        return False, f"❌ Token count ({result.count:,}) exceeds model limit"
    
    if result.estimated_cost_usd > max_cost_usd:
        return False, f"❌ Estimated cost (${result.estimated_cost_usd:.6f}) exceeds budget (${max_cost_usd})"
    
    if result.estimated_latency_sec > max_latency_sec:
        return False, f"❌ Estimated latency ({result.estimated_latency_sec:.1f}s) exceeds limit ({max_latency_sec}s)"
    
    return True, f"✅ Request valid (tokens: {result.count:,}, cost: ${result.estimated_cost_usd:.6f}, latency: {result.estimated_latency_sec:.1f}s)"


def truncate_to_budget(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    """
    Truncate text to fit within token budget.
    
    Args:
        text: Input text
        max_tokens: Maximum allowed tokens
        model: Model name
        
    Returns:
        Truncated text
    """
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    
    if len(tokens) <= max_tokens:
        return text
    
    # Truncate and decode
    truncated_tokens = tokens[:max_tokens]
    truncated_text = enc.decode(truncated_tokens)
    
    return truncated_text + "... [truncated]"


def main():
    """Run token counting demos."""
    print("="*70)
    print("🔢 TOKEN COUNTING & BUDGET ENFORCEMENT")
    print("="*70)
    
    # Demo 1: Count tokens for different texts
    print("\n" + "="*70)
    print("Demo 1: Token Counting")
    print("="*70)
    
    texts = {
        "Short": "Hello, world!",
        "Medium": "Artificial intelligence is transforming how we live and work. " * 5,
        "Long": "The future of AI is bright and full of possibilities. " * 100,
    }
    
    for name, text in texts.items():
        token_count = count_tokens(text)
        char_count = len(text)
        print(f"\n{name} text:")
        print(f"  Characters: {char_count:,}")
        print(f"  Tokens: {token_count:,}")
        print(f"  Ratio: {char_count/token_count:.2f} chars/token")
    
    # Demo 2: Budget enforcement
    print("\n" + "="*70)
    print("Demo 2: Budget Enforcement")
    print("="*70)
    
    test_cases = [
        ("Hello, world!", "gpt-4", 100),
        ("The quick brown fox. " * 1000, "gpt-3.5-turbo", 500),
        ("Long document. " * 10000, "gpt-4", 1000),
    ]
    
    for text, model, expected_output in test_cases:
        result = check_token_budget(text, model, expected_output)
        status = "✅ PASS" if result.within_budget else "❌ FAIL"
        
        print(f"\n{status} | Model: {model}")
        print(f"  Input tokens: {result.count:,}")
        print(f"  Expected output: {expected_output:,}")
        print(f"  Within budget: {result.within_budget}")
        print(f"  Estimated cost: ${result.estimated_cost_usd:.6f}")
        print(f"  Estimated latency: {result.estimated_latency_sec:.1f}s")
    
    # Demo 3: Request validation
    print("\n" + "="*70)
    print("Demo 3: Request Validation")
    print("="*70)
    
    requests = [
        {
            "text": "Summarize this: " + "AI is amazing. " * 10,
            "model": "gpt-3.5-turbo",
            "max_cost": 0.01,
            "max_latency": 5.0,
        },
        {
            "text": "Analyze this: " + "Data point. " * 1000,
            "model": "gpt-4",
            "max_cost": 0.001,  # Very low budget
            "max_latency": 10.0,
        },
        {
            "text": "Translate: " + "Hello world. " * 100,
            "model": "claude-haiku",
            "max_cost": 0.01,
            "max_latency": 2.0,  # Very low latency
        },
    ]
    
    for i, req in enumerate(requests, 1):
        valid, message = validate_request(
            req["text"],
            req["model"],
            req["max_cost"],
            req["max_latency"],
        )
        
        print(f"\nRequest {i}: {message}")
    
    # Demo 4: Truncation
    print("\n" + "="*70)
    print("Demo 4: Text Truncation")
    print("="*70)
    
    long_text = "This is a very long document. " * 500
    original_count = count_tokens(long_text)
    
    print(f"\nOriginal text:")
    print(f"  Tokens: {original_count:,}")
    
    max_tokens = 100
    truncated = truncate_to_budget(long_text, max_tokens)
    truncated_count = count_tokens(truncated)
    
    print(f"\nTruncated text (max {max_tokens} tokens):")
    print(f"  Tokens: {truncated_count:,}")
    print(f"  Preview: {truncated[:100]}...")
    
    # Demo 5: Model comparison
    print("\n" + "="*70)
    print("Demo 5: Model Budget Comparison")
    print("="*70)
    
    sample_text = "Analyze this data: " + "point, " * 1000
    
    print(f"\nSample text: {count_tokens(sample_text):,} tokens")
    print("\nModel budgets:")
    
    for model_name, config in MODEL_CONFIGS.items():
        result = check_token_budget(sample_text, model_name, 500)
        print(f"\n{model_name}:")
        print(f"  Max input: {config.max_input_tokens:,} tokens")
        print(f"  Within budget: {'✅ Yes' if result.within_budget else '❌ No'}")
        print(f"  Estimated cost: ${result.estimated_cost_usd:.6f}")
    
    print("\n" + "="*70)
    print("✅ Demo complete!")
    print("="*70)
    print("\nKey takeaways:")
    print("  • Always count tokens before API calls")
    print("  • Enforce budget limits to prevent cost overruns")
    print("  • Check context window limits to prevent failures")
    print("  • Truncate text if needed to fit budget")
    print("  • Different models have different limits and costs")


if __name__ == "__main__":
    main()
