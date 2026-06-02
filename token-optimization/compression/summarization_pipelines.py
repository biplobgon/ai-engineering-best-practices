"""
Recursive summarization: Multi-pass compression using LLMs.

This module provides LLM-powered compression that progressively reduces
token count while preserving key information.

Performance:
- Reduction: 60-80% per pass
- Latency: 2-5s per pass
- Quality: Medium (some information loss acceptable)
"""

import asyncio
import logging
from typing import Optional

from core.llm import chat
from token_optimization.compression.token_pruning import count_tokens


logger = logging.getLogger(__name__)


# Summarization prompts
SUMMARIZE_PROMPT = """Summarize the following text concisely while preserving key information.
Focus on facts, decisions, and actionable insights. Remove redundancy and filler.

Target length: {target_tokens} tokens (you currently have {current_tokens} tokens to compress).

Text:
{text}

Summary:"""


RECURSIVE_PROMPT = """You are compressing text for a context window. 
Summarize the following content to approximately {target_tokens} tokens.
Preserve the most important information and remove redundancy.

Content:
{text}

Compressed version:"""


async def summarize_once(
    text: str,
    target_tokens: int,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> str:
    """
    Single-pass summarization.
    
    Args:
        text: Input text
        target_tokens: Target token count
        model: LLM model to use
        temperature: Lower = more deterministic
        
    Returns:
        Summarized text
    """
    current_tokens = count_tokens(text)
    
    if current_tokens <= target_tokens:
        return text
    
    prompt = SUMMARIZE_PROMPT.format(
        target_tokens=target_tokens,
        current_tokens=current_tokens,
        text=text,
    )
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        response = await chat(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=target_tokens * 2,  # Give headroom
        )
        
        summary = response.text.strip()
        
        logger.info(
            f"Summarized {current_tokens} → {count_tokens(summary)} tokens "
            f"({(1 - count_tokens(summary)/current_tokens)*100:.1f}% reduction)"
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        # Fallback: truncate to target
        return text[:target_tokens * 4]  # ~4 chars per token


async def recursive_summarize(
    text: str,
    target_tokens: int,
    max_passes: int = 3,
    model: str = "gpt-4o-mini",
    compression_ratio: float = 0.5,
) -> str:
    """
    Multi-pass recursive summarization.
    
    Strategy:
    1. If text fits target, return as-is
    2. Otherwise, compress by `compression_ratio` (default 50%)
    3. Repeat until target reached or max_passes exhausted
    
    Args:
        text: Input text
        target_tokens: Target token count
        max_passes: Maximum compression passes
        model: LLM model to use
        compression_ratio: Target compression per pass (0.5 = 50% reduction)
        
    Returns:
        Recursively compressed text
        
    Example:
        >>> doc = load_document()  # 10,000 tokens
        >>> compressed = await recursive_summarize(doc, target_tokens=1000)
        >>> # Pass 1: 10,000 → 5,000
        >>> # Pass 2: 5,000 → 2,500
        >>> # Pass 3: 2,500 → 1,250
        >>> # Final: ~1,250 tokens
    """
    current = text
    current_tokens = count_tokens(current)
    
    if current_tokens <= target_tokens:
        logger.info(f"Text already within target ({current_tokens} <= {target_tokens})")
        return current
    
    for pass_num in range(1, max_passes + 1):
        # Calculate intermediate target
        if pass_num == max_passes:
            # Last pass: hit target exactly
            intermediate_target = target_tokens
        else:
            # Intermediate: compress by ratio
            intermediate_target = int(current_tokens * compression_ratio)
        
        logger.info(f"Pass {pass_num}/{max_passes}: {current_tokens} → {intermediate_target} tokens")
        
        current = await summarize_once(
            current,
            target_tokens=intermediate_target,
            model=model,
        )
        
        current_tokens = count_tokens(current)
        
        # Early exit if target reached
        if current_tokens <= target_tokens:
            logger.info(f"Target reached after {pass_num} passes")
            break
    
    final_tokens = count_tokens(current)
    original_tokens = count_tokens(text)
    reduction_pct = (1 - final_tokens / original_tokens) * 100
    
    logger.info(
        f"Recursive summarization complete: "
        f"{original_tokens} → {final_tokens} tokens ({reduction_pct:.1f}% reduction)"
    )
    
    return current


async def chunk_and_summarize(
    text: str,
    chunk_size: int = 4000,
    target_tokens: int = 1000,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Split into chunks, summarize each, then combine.
    
    Useful for very long documents where single-pass fails.
    
    Args:
        text: Input text
        chunk_size: Tokens per chunk
        target_tokens: Final target token count
        model: LLM model
        
    Returns:
        Combined summary
        
    Strategy:
        1. Split text into chunks of `chunk_size`
        2. Summarize each chunk independently
        3. Combine summaries
        4. If still too long, summarize the combined summaries
    """
    current_tokens = count_tokens(text)
    
    if current_tokens <= chunk_size:
        # No chunking needed
        return await summarize_once(text, target_tokens, model)
    
    # Split into chunks (rough split by characters)
    chars_per_chunk = chunk_size * 4  # ~4 chars per token
    chunks = [text[i:i+chars_per_chunk] for i in range(0, len(text), chars_per_chunk)]
    
    logger.info(f"Split into {len(chunks)} chunks of ~{chunk_size} tokens each")
    
    # Summarize each chunk in parallel
    summary_tasks = [
        summarize_once(chunk, target_tokens=chunk_size // 2, model=model)
        for chunk in chunks
    ]
    
    summaries = await asyncio.gather(*summary_tasks)
    
    # Combine summaries
    combined = "\n\n".join(summaries)
    combined_tokens = count_tokens(combined)
    
    logger.info(f"Combined summaries: {combined_tokens} tokens")
    
    # If combined is still too long, do final pass
    if combined_tokens > target_tokens:
        combined = await summarize_once(combined, target_tokens, model)
    
    return combined


async def adaptive_summarize(
    text: str,
    target_tokens: int,
    model: str = "gpt-4o-mini",
    max_latency_ms: Optional[int] = None,
) -> str:
    """
    Automatically choose best summarization strategy based on text length.
    
    Args:
        text: Input text
        target_tokens: Target token count
        model: LLM model
        max_latency_ms: If specified, use faster methods for time-sensitive tasks
        
    Returns:
        Summarized text
        
    Strategy:
        - Small text (< 2x target): Single pass
        - Medium text (2-10x target): Recursive (2-3 passes)
        - Large text (> 10x target): Chunk and summarize
    """
    current_tokens = count_tokens(text)
    ratio = current_tokens / target_tokens
    
    logger.info(f"Adaptive summarization: {current_tokens} tokens, ratio={ratio:.1f}x")
    
    if ratio <= 1.0:
        # Already within target
        return text
    elif ratio <= 2.0:
        # Single pass sufficient
        return await summarize_once(text, target_tokens, model)
    elif ratio <= 10.0:
        # Recursive works well
        max_passes = 3 if ratio <= 5.0 else 4
        return await recursive_summarize(text, target_tokens, max_passes, model)
    else:
        # Very long: chunk first
        return await chunk_and_summarize(text, target_tokens=target_tokens, model=model)


# Metrics wrapper
async def summarize_with_metrics(
    text: str,
    target_tokens: int,
    method: str = "recursive",
    **kwargs
) -> dict:
    """
    Summarize and return metrics.
    
    Args:
        text: Input text
        target_tokens: Target token count
        method: "once", "recursive", "chunk", or "adaptive"
        **kwargs: Passed to summarization function
        
    Returns:
        Dict with:
        - text: Summarized text
        - tokens_before: Original tokens
        - tokens_after: Compressed tokens
        - reduction_pct: Percentage reduction
        - latency_ms: Time taken
    """
    import time
    
    tokens_before = count_tokens(text)
    start = time.perf_counter()
    
    if method == "once":
        result = await summarize_once(text, target_tokens, **kwargs)
    elif method == "recursive":
        result = await recursive_summarize(text, target_tokens, **kwargs)
    elif method == "chunk":
        result = await chunk_and_summarize(text, target_tokens, **kwargs)
    elif method == "adaptive":
        result = await adaptive_summarize(text, target_tokens, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    latency_ms = (time.perf_counter() - start) * 1000
    tokens_after = count_tokens(result)
    reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
    
    return {
        'text': result,
        'tokens_before': tokens_before,
        'tokens_after': tokens_after,
        'reduction_pct': round(reduction_pct, 2),
        'latency_ms': round(latency_ms, 2),
        'method': method,
    }


# Example usage
if __name__ == "__main__":
    # Demo (requires LLM setup)
    async def demo():
        sample_text = """
        Artificial intelligence has made remarkable progress in recent years, 
        with large language models demonstrating unprecedented capabilities in 
        natural language understanding and generation. These models, trained on 
        vast amounts of text data, can perform a wide variety of tasks including 
        translation, summarization, question answering, and code generation.
        
        However, the deployment of these models comes with significant challenges.
        One major issue is the cost associated with running large models, which 
        can be prohibitively expensive for many applications. Token usage directly
        impacts cost, as most API providers charge per token processed.
        
        Another challenge is latency. Large models can take several seconds to 
        generate responses, which is unacceptable for real-time applications.
        Various optimization techniques have been developed to address these issues,
        including model distillation, quantization, and prompt compression.
        
        This document explores token optimization strategies that can reduce costs
        by 60-80% while maintaining acceptable quality levels.
        """ * 10  # Repeat to make it longer
        
        print("Recursive Summarization Demo\n" + "="*60)
        
        result = await summarize_with_metrics(
            sample_text,
            target_tokens=200,
            method="recursive",
        )
        
        print(f"\nOriginal: {result['tokens_before']} tokens")
        print(f"Compressed: {result['tokens_after']} tokens")
        print(f"Reduction: {result['reduction_pct']}%")
        print(f"Latency: {result['latency_ms']}ms")
        print(f"\nSummary:\n{result['text']}")
    
    # Uncomment to run:
    # asyncio.run(demo())
    print("Demo available - uncomment asyncio.run(demo()) to test")
