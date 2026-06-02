"""
Sliding Window: Handle long documents with overlapping windows.

This script demonstrates:
1. Splitting long documents into overlapping chunks
2. Processing each chunk while maintaining context
3. Combining results with deduplication
4. Handling boundary conditions

Run: python sliding_window.py
"""

import asyncio
import tiktoken
from typing import List, Dict, Tuple
from dataclasses import dataclass

from core.llm import chat
from core.config import get_settings


@dataclass
class WindowChunk:
    """Represents a window chunk of text."""
    text: str
    start_pos: int
    end_pos: int
    token_count: int
    chunk_id: int


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    
    return len(enc.encode(text))


def split_into_windows(
    text: str,
    window_size: int = 10000,
    overlap: int = 1000,
    model: str = "gpt-4",
) -> List[WindowChunk]:
    """
    Split text into overlapping windows.
    
    Args:
        text: Input text
        window_size: Window size in tokens
        overlap: Overlap size in tokens
        model: Model for tokenization
        
    Returns:
        List of WindowChunk objects
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    
    # Tokenize full text
    tokens = enc.encode(text)
    total_tokens = len(tokens)
    
    if total_tokens <= window_size:
        # Document fits in one window
        return [
            WindowChunk(
                text=text,
                start_pos=0,
                end_pos=total_tokens,
                token_count=total_tokens,
                chunk_id=0,
            )
        ]
    
    # Create overlapping windows
    windows = []
    chunk_id = 0
    start = 0
    
    while start < total_tokens:
        end = min(start + window_size, total_tokens)
        
        # Extract window tokens and decode
        window_tokens = tokens[start:end]
        window_text = enc.decode(window_tokens)
        
        windows.append(
            WindowChunk(
                text=window_text,
                start_pos=start,
                end_pos=end,
                token_count=len(window_tokens),
                chunk_id=chunk_id,
            )
        )
        
        # Move to next window (with overlap)
        if end >= total_tokens:
            break
        
        start += window_size - overlap
        chunk_id += 1
    
    return windows


async def process_window(
    chunk: WindowChunk,
    instruction: str,
    model: str = "gpt-4o-mini",
) -> Dict[str, any]:
    """
    Process a single window chunk.
    
    Args:
        chunk: Window chunk to process
        instruction: Processing instruction
        model: Model to use
        
    Returns:
        Processing result
    """
    prompt = f"{instruction}\n\nText:\n{chunk.text}"
    
    try:
        result = await chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3,
            max_tokens=500,
        )
        
        return {
            "chunk_id": chunk.chunk_id,
            "result": result.text,
            "tokens_in": result.tokens_in,
            "tokens_out": result.tokens_out,
            "cost_usd": result.usd_cost,
        }
    except Exception as e:
        return {
            "chunk_id": chunk.chunk_id,
            "result": f"[Error: {e}]",
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
        }


async def process_with_sliding_window(
    text: str,
    instruction: str,
    window_size: int = 10000,
    overlap: int = 1000,
    model: str = "gpt-4o-mini",
) -> Dict[str, any]:
    """
    Process long document using sliding window approach.
    
    Args:
        text: Input document
        instruction: Processing instruction (e.g., "Summarize this text")
        window_size: Window size in tokens
        overlap: Overlap size in tokens
        model: Model to use
        
    Returns:
        Combined results
    """
    # Split into windows
    windows = split_into_windows(text, window_size, overlap)
    
    print(f"Split document into {len(windows)} windows")
    print(f"Window size: {window_size} tokens, Overlap: {overlap} tokens")
    
    # Process each window
    results = []
    total_cost = 0.0
    
    for i, chunk in enumerate(windows):
        print(f"Processing window {i+1}/{len(windows)}...")
        result = await process_window(chunk, instruction, model)
        results.append(result)
        total_cost += result["cost_usd"]
    
    return {
        "windows": windows,
        "results": results,
        "total_windows": len(windows),
        "total_cost_usd": total_cost,
    }


def combine_results(results: List[Dict], strategy: str = "concatenate") -> str:
    """
    Combine results from multiple windows.
    
    Args:
        results: List of processing results
        strategy: Combination strategy (concatenate, merge, deduplicate)
        
    Returns:
        Combined result
    """
    if strategy == "concatenate":
        # Simple concatenation
        return "\n\n".join([r["result"] for r in results if r["result"]])
    
    elif strategy == "deduplicate":
        # Remove duplicate sentences
        all_text = []
        seen_sentences = set()
        
        for r in results:
            sentences = r["result"].split(". ")
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and sentence not in seen_sentences:
                    all_text.append(sentence)
                    seen_sentences.add(sentence)
        
        return ". ".join(all_text)
    
    else:
        # Default to concatenate
        return "\n\n".join([r["result"] for r in results if r["result"]])


async def demo_basic_sliding_window():
    """Demo: Basic sliding window processing."""
    print("="*90)
    print("DEMO 1: Basic Sliding Window")
    print("="*90)
    
    # Create a long document (simulate)
    paragraph = """
    Artificial intelligence has revolutionized how we interact with technology.
    From virtual assistants to recommendation systems, AI is everywhere. Machine
    learning models can now understand natural language, generate images, and even
    write code. The field continues to evolve rapidly, with new breakthroughs
    happening regularly. Large language models like GPT have shown remarkable
    capabilities in understanding and generating human-like text.
    """
    
    # Repeat to make it longer
    long_doc = (paragraph * 20).strip()
    
    print(f"\nDocument length: {count_tokens(long_doc)} tokens")
    
    # Split into windows
    windows = split_into_windows(long_doc, window_size=500, overlap=100)
    
    print(f"\nSplit into {len(windows)} windows:")
    for i, window in enumerate(windows):
        print(f"  Window {i}: tokens {window.start_pos}-{window.end_pos} ({window.token_count} tokens)")


async def demo_process_with_windows():
    """Demo: Process document with sliding windows."""
    print("\n" + "="*90)
    print("DEMO 2: Process with Sliding Windows")
    print("="*90)
    
    settings = get_settings()
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        print("\n⚠️  Skipping live processing (no API keys found)")
        return
    
    # Sample document
    document = """
    Climate change is one of the most pressing issues of our time. Rising global
    temperatures are causing glaciers to melt, sea levels to rise, and weather
    patterns to become more extreme. Scientists have documented these changes
    extensively, showing clear evidence of human impact on the climate.
    
    The consequences of climate change are far-reaching. Coastal cities face
    flooding risks, agricultural regions experience droughts, and ecosystems
    struggle to adapt. Many species are threatened with extinction as their
    habitats change faster than they can evolve.
    
    Addressing climate change requires global cooperation. Countries must reduce
    greenhouse gas emissions, transition to renewable energy, and develop
    sustainable practices. Individual actions also matter - reducing waste,
    conserving energy, and supporting eco-friendly policies all contribute
    to the solution.
    """ * 5  # Repeat to make longer
    
    print(f"\nDocument: {count_tokens(document)} tokens")
    
    result = await process_with_sliding_window(
        text=document,
        instruction="Extract the main points from this text in bullet format:",
        window_size=300,
        overlap=50,
    )
    
    print(f"\nProcessing complete:")
    print(f"  Total windows: {result['total_windows']}")
    print(f"  Total cost: ${result['total_cost_usd']:.6f}")
    
    # Combine results
    combined = combine_results(result['results'], strategy="deduplicate")
    print(f"\nCombined result:")
    print(combined[:500] + "..." if len(combined) > 500 else combined)


async def demo_overlap_importance():
    """Demo: Importance of overlap."""
    print("\n" + "="*90)
    print("DEMO 3: Overlap Importance")
    print("="*90)
    
    text = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z " * 100
    
    print(f"\nDocument: {count_tokens(text)} tokens")
    
    # No overlap
    windows_no_overlap = split_into_windows(text, window_size=200, overlap=0)
    print(f"\nNo overlap: {len(windows_no_overlap)} windows")
    for i, w in enumerate(windows_no_overlap[:3]):
        print(f"  Window {i}: {w.start_pos}-{w.end_pos}")
    
    # With overlap
    windows_with_overlap = split_into_windows(text, window_size=200, overlap=50)
    print(f"\nWith 50-token overlap: {len(windows_with_overlap)} windows")
    for i, w in enumerate(windows_with_overlap[:3]):
        print(f"  Window {i}: {w.start_pos}-{w.end_pos}")
    
    print("\nBenefit of overlap:")
    print("  • Maintains context between windows")
    print("  • Prevents information loss at boundaries")
    print("  • Improves result quality")


async def demo_cost_comparison():
    """Demo: Cost comparison of different approaches."""
    print("\n" + "="*90)
    print("DEMO 4: Cost Comparison")
    print("="*90)
    
    # Simulate a 150K token document
    doc_tokens = 150_000
    
    # Model context limit
    context_limit = 128_000
    
    print(f"\nScenario: {doc_tokens:,} token document")
    print(f"Model: GPT-4o-mini (context limit: {context_limit:,} tokens)")
    
    # Approach 1: Direct (fails)
    print(f"\nApproach 1: Direct processing")
    print(f"  ❌ Fails - exceeds context limit")
    
    # Approach 2: Sliding windows
    window_size = 100_000
    overlap = 10_000
    num_windows = ((doc_tokens - overlap) // (window_size - overlap)) + 1
    
    # Cost per window (assuming 500 token output)
    input_cost_per_1m = 0.15
    output_cost_per_1m = 0.60
    
    input_cost = (window_size / 1_000_000) * input_cost_per_1m
    output_cost = (500 / 1_000_000) * output_cost_per_1m
    cost_per_window = input_cost + output_cost
    
    total_cost_windows = cost_per_window * num_windows
    
    print(f"\nApproach 2: Sliding windows")
    print(f"  Window size: {window_size:,} tokens")
    print(f"  Overlap: {overlap:,} tokens")
    print(f"  Number of windows: {num_windows}")
    print(f"  Cost per window: ${cost_per_window:.6f}")
    print(f"  Total cost: ${total_cost_windows:.4f}")
    
    # Approach 3: Pruning + single call
    pruned_tokens = 100_000
    pruned_cost = ((pruned_tokens / 1_000_000) * input_cost_per_1m +
                   (500 / 1_000_000) * output_cost_per_1m)
    
    print(f"\nApproach 3: Prune to {pruned_tokens:,} tokens")
    print(f"  Single API call")
    print(f"  Total cost: ${pruned_cost:.6f}")
    print(f"  Savings vs windows: ${total_cost_windows - pruned_cost:.6f}")


async def main():
    """Run all sliding window demos."""
    print("="*90)
    print("🪟 SLIDING WINDOW DEMO")
    print("="*90)
    
    await demo_basic_sliding_window()
    await demo_process_with_windows()
    await demo_overlap_importance()
    await demo_cost_comparison()
    
    print("\n" + "="*90)
    print("✅ Demo complete!")
    print("="*90)
    print("\nKey takeaways:")
    print("  • Sliding windows handle documents exceeding context limits")
    print("  • Overlap maintains context between windows")
    print("  • More windows = higher cost and latency")
    print("  • Combine results with deduplication")
    print("  • Consider pruning as an alternative")


if __name__ == "__main__":
    asyncio.run(main())
