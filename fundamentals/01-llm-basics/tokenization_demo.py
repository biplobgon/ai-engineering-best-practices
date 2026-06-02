"""
Tokenization Demo: Hands-on exploration of how different models tokenize text.

This script demonstrates:
1. How to tokenize text with tiktoken (OpenAI models)
2. Token count differences between models
3. Visualization of token boundaries
4. Cost estimation from token counts

Run: python tokenization_demo.py
"""

import tiktoken
from typing import List


def tokenize_with_gpt4(text: str) -> tuple[List[int], List[str]]:
    """Tokenize text using GPT-4 tokenizer."""
    enc = tiktoken.encoding_for_model("gpt-4")
    token_ids = enc.encode(text)
    # Decode each token to see the text
    tokens = [enc.decode([tid]) for tid in token_ids]
    return token_ids, tokens


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens for a given model."""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def visualize_tokens(text: str) -> None:
    """Show token boundaries with visual separators."""
    enc = tiktoken.encoding_for_model("gpt-4")
    token_ids = enc.encode(text)
    tokens = [enc.decode([tid]) for tid in token_ids]
    
    print(f"\n📝 Original text ({len(text)} chars):")
    print(f'   "{text}"')
    print(f"\n🔢 Tokenized ({len(tokens)} tokens):")
    print(f'   {"|".join(f"[{t}]" for t in tokens)}')
    print(f"\n💡 Token IDs: {token_ids}")


def compare_content_types() -> None:
    """Compare token counts across different content types."""
    examples = {
        "English prose": "The quick brown fox jumps over the lazy dog. This is a simple sentence.",
        "Python code": "def calculate_sum(x, y):\n    return x + y\n\nresult = calculate_sum(10, 20)",
        "JSON data": '{"name": "John Doe", "age": 30, "email": "john@example.com", "active": true}',
        "Emoji text": "Hello 👋 world 🌍! How are you today? 😊",
    }
    
    print("\n" + "="*70)
    print("Token Counts by Content Type")
    print("="*70)
    
    for content_type, text in examples.items():
        token_count = count_tokens(text)
        char_count = len(text)
        ratio = char_count / token_count if token_count > 0 else 0
        
        print(f"\n{content_type}:")
        print(f"  Text: {text[:50]}..." if len(text) > 50 else f"  Text: {text}")
        print(f"  Chars: {char_count:,} | Tokens: {token_count:,} | Ratio: {ratio:.2f} chars/token")


def estimate_cost(text: str, price_per_1m_tokens: float = 3.0) -> dict:
    """Estimate cost for processing text."""
    token_count = count_tokens(text)
    cost_usd = (token_count / 1_000_000) * price_per_1m_tokens
    
    return {
        "tokens": token_count,
        "cost_usd": cost_usd,
        "price_per_1m": price_per_1m_tokens
    }


def main():
    """Run all tokenization demos."""
    print("="*70)
    print("🔤 TOKENIZATION DEMO")
    print("="*70)
    
    # Demo 1: Basic tokenization
    print("\n" + "="*70)
    print("Demo 1: Basic Tokenization")
    print("="*70)
    
    text = "Hello, world! How are you today?"
    token_ids, tokens = tokenize_with_gpt4(text)
    
    print(f"\nOriginal text: \"{text}\"")
    print(f"Token count: {len(tokens)}")
    print(f"Tokens: {tokens}")
    print(f"Token IDs: {token_ids[:10]}...")  # First 10 IDs
    
    # Demo 2: Visualize token boundaries
    print("\n" + "="*70)
    print("Demo 2: Token Boundaries")
    print("="*70)
    
    examples = [
        "Hello, world!",
        "superintelligent",
        "The quick brown fox",
        "def function(x): return x**2",
    ]
    
    for example in examples:
        visualize_tokens(example)
    
    # Demo 3: Compare content types
    compare_content_types()
    
    # Demo 4: Cost estimation
    print("\n" + "="*70)
    print("Demo 4: Cost Estimation")
    print("="*70)
    
    document = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, 
    in contrast to the natural intelligence displayed by humans and animals. 
    Leading AI textbooks define the field as the study of "intelligent agents": 
    any device that perceives its environment and takes actions that maximize 
    its chance of successfully achieving its goals.
    """ * 10  # Repeat to make it longer
    
    cost_info = estimate_cost(document, price_per_1m_tokens=3.0)
    
    print(f"\nDocument length: {len(document):,} characters")
    print(f"Token count: {cost_info['tokens']:,}")
    print(f"Estimated cost: ${cost_info['cost_usd']:.6f} USD")
    print(f"(at ${cost_info['price_per_1m']}/1M tokens)")
    
    # Demo 5: Rule of thumb validation
    print("\n" + "="*70)
    print("Demo 5: Rule of Thumb Validation")
    print("="*70)
    
    text_sample = "The quick brown fox jumps over the lazy dog. " * 20
    chars = len(text_sample)
    tokens = count_tokens(text_sample)
    words = len(text_sample.split())
    
    print(f"\nSample text (repeated sentence):")
    print(f"  Characters: {chars:,}")
    print(f"  Words: {words:,}")
    print(f"  Tokens: {tokens:,}")
    print(f"\nRatios:")
    print(f"  Chars/Token: {chars/tokens:.2f} (rule of thumb: ~4)")
    print(f"  Words/Token: {words/tokens:.2f} (rule of thumb: ~0.75)")
    print(f"  Tokens/Word: {tokens/words:.2f} (rule of thumb: ~1.33)")
    
    print("\n" + "="*70)
    print("✅ Demo complete!")
    print("="*70)
    print("\nKey takeaways:")
    print("  • 1 token ≈ 4 characters (English)")
    print("  • 1 token ≈ 0.75 words")
    print("  • Different content types have different token densities")
    print("  • Always count tokens for accurate cost estimation")


if __name__ == "__main__":
    main()
