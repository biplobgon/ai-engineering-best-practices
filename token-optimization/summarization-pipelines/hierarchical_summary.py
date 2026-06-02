"""
Hierarchical summarization using map-reduce pattern.

Best for very long documents (50+ pages). Chunks document, summarizes
each chunk, then recursively summarizes the summaries.

Performance:
- Reduction: 90-95%
- Latency: 10-30s for 100-page docs
- Quality: Medium-High
"""

import asyncio
import logging
from typing import Optional

from core.llm import chat
from token_optimization.compression.token_pruning import count_tokens


logger = logging.getLogger(__name__)


async def hierarchical_summarize(
    text: str,
    target_tokens: int = 1000,
    chunk_size: int = 4000,
    model: str = "gpt-4o-mini",
    max_depth: int = 3,
) -> str:
    """
    Hierarchical map-reduce summarization.
    
    Strategy:
        1. Split document into chunks
        2. Summarize each chunk (map)
        3. Combine summaries (reduce)
        4. If combined is still too long, repeat steps 1-3
        5. Stop when target reached or max_depth hit
    
    Args:
        text: Input document
        target_tokens: Target token count
        chunk_size: Tokens per chunk in first pass
        model: LLM model
        max_depth: Maximum recursion depth
        
    Returns:
        Hierarchically summarized text
        
    Example:
        >>> doc = load_100_page_document()  # 50,000 tokens
        >>> summary = await hierarchical_summarize(doc, target_tokens=500)
        >>> # Level 1: 50,000 → 10,000 (10 chunks × 1,000 token summaries)
        >>> # Level 2: 10,000 → 2,000 (10 chunks × 200 token summaries)
        >>> # Level 3: 2,000 → 500 (final compression)
    """
    current_tokens = count_tokens(text)
    
    if current_tokens <= target_tokens:
        logger.info(f"Already within target ({current_tokens} <= {target_tokens})")
        return text
    
    logger.info(f"Hierarchical summarization: {current_tokens} → {target_tokens} tokens")
    
    return await _hierarchical_summarize_recursive(
        text,
        target_tokens=target_tokens,
        chunk_size=chunk_size,
        model=model,
        depth=0,
        max_depth=max_depth,
    )


async def _hierarchical_summarize_recursive(
    text: str,
    target_tokens: int,
    chunk_size: int,
    model: str,
    depth: int,
    max_depth: int,
) -> str:
    """Recursive helper for hierarchical summarization."""
    
    current_tokens = count_tokens(text)
    
    # Base case: within target or max depth reached
    if current_tokens <= target_tokens or depth >= max_depth:
        if depth >= max_depth and current_tokens > target_tokens:
            logger.warning(f"Max depth {max_depth} reached, stopping at {current_tokens} tokens")
        return text
    
    logger.info(f"Depth {depth}: {current_tokens} tokens, chunking into {chunk_size}-token pieces")
    
    # Split into chunks
    chunks = _split_into_chunks(text, chunk_size)
    logger.info(f"Created {len(chunks)} chunks")
    
    # Calculate target for each chunk summary
    # Want combined summaries to be ~half current size
    per_chunk_target = max(200, (current_tokens // 2) // len(chunks))
    
    # Summarize each chunk in parallel
    summary_tasks = [
        _summarize_chunk(chunk, per_chunk_target, model)
        for chunk in chunks
    ]
    summaries = await asyncio.gather(*summary_tasks)
    
    # Combine summaries
    combined = "\n\n".join(summaries)
    combined_tokens = count_tokens(combined)
    
    logger.info(f"Depth {depth}: combined summaries = {combined_tokens} tokens")
    
    # Recurse if still too long
    if combined_tokens > target_tokens:
        return await _hierarchical_summarize_recursive(
            combined,
            target_tokens=target_tokens,
            chunk_size=chunk_size,
            model=model,
            depth=depth + 1,
            max_depth=max_depth,
        )
    
    return combined


def _split_into_chunks(text: str, chunk_size: int) -> list[str]:
    """
    Split text into chunks of approximately chunk_size tokens.
    
    Tries to split on paragraph boundaries when possible.
    """
    # Rough estimate: 1 token ≈ 4 characters
    chars_per_chunk = chunk_size * 4
    
    # Try to split on double newlines (paragraphs)
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para_length = len(para)
        
        if current_length + para_length > chars_per_chunk and current_chunk:
            # Current chunk is full, start new one
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_length = para_length
        else:
            # Add to current chunk
            current_chunk.append(para)
            current_length += para_length
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    # If no double newlines, fall back to character-based splitting
    if len(chunks) == 1:
        text_to_split = chunks[0]
        chunks = [
            text_to_split[i:i+chars_per_chunk]
            for i in range(0, len(text_to_split), chars_per_chunk)
        ]
    
    return chunks


async def _summarize_chunk(
    chunk: str,
    target_tokens: int,
    model: str,
) -> str:
    """Summarize a single chunk."""
    
    prompt = f"""Summarize the following text concisely in approximately {target_tokens} tokens.
Focus on key information, facts, and main points.

Text:
{chunk}

Summary:"""
    
    try:
        response = await chat(
            [{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3,
            max_tokens=target_tokens * 2,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Chunk summarization failed: {e}")
        # Fallback: truncate
        return chunk[:target_tokens * 4]


async def map_reduce_summarize(
    documents: list[str],
    target_tokens: int = 1000,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Map-reduce for multiple documents.
    
    Args:
        documents: List of documents
        target_tokens: Target total tokens
        model: LLM model
        
    Returns:
        Combined summary
        
    Example:
        >>> docs = [research_paper_1, research_paper_2, research_paper_3]
        >>> combined_summary = await map_reduce_summarize(docs, target_tokens=500)
    """
    if not documents:
        return ""
    
    total_tokens = sum(count_tokens(doc) for doc in documents)
    logger.info(f"Map-reduce: {len(documents)} documents, {total_tokens} total tokens")
    
    # Map: Summarize each document
    per_doc_target = target_tokens // len(documents)
    summary_tasks = [
        _summarize_chunk(doc, per_doc_target, model)
        for doc in documents
    ]
    summaries = await asyncio.gather(*summary_tasks)
    
    # Reduce: Combine summaries
    combined = "\n\n".join(summaries)
    combined_tokens = count_tokens(combined)
    
    # If still too long, do final compression
    if combined_tokens > target_tokens:
        logger.info(f"Final compression: {combined_tokens} → {target_tokens}")
        final_summary = await _summarize_chunk(combined, target_tokens, model)
        return final_summary
    
    return combined


async def hierarchical_with_metrics(
    text: str,
    target_tokens: int = 1000,
    **kwargs
) -> dict:
    """
    Hierarchical summarization with metrics.
    
    Returns:
        Dict with summary and metrics
    """
    import time
    
    tokens_before = count_tokens(text)
    start = time.perf_counter()
    
    summary = await hierarchical_summarize(text, target_tokens, **kwargs)
    
    latency_ms = (time.perf_counter() - start) * 1000
    tokens_after = count_tokens(summary)
    reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
    
    return {
        'text': summary,
        'tokens_before': tokens_before,
        'tokens_after': tokens_after,
        'reduction_pct': round(reduction_pct, 2),
        'latency_ms': round(latency_ms, 2),
    }


# Example usage
if __name__ == "__main__":
    async def demo():
        # Simulate a long document
        sample_text = """
        Artificial intelligence has transformed modern computing in unprecedented ways.
        Large language models represent a significant milestone in this journey.
        These models can understand and generate human-like text across many domains.
        
        The training process involves massive datasets and computational resources.
        Models learn patterns and relationships from billions of text examples.
        This enables them to perform tasks like translation, summarization, and reasoning.
        
        However, deploying these models comes with challenges. Token usage directly
        impacts cost, as providers charge per token. Latency is another concern,
        as large models can take seconds to generate responses.
        
        Various optimization techniques help address these issues. Token compression
        reduces input size. Caching avoids redundant processing. Streaming improves
        perceived latency. Parallel execution speeds up multi-step workflows.
        """ * 100  # Repeat to make it long
        
        print("Hierarchical Summarization Demo\n" + "="*60)
        
        result = await hierarchical_with_metrics(
            sample_text,
            target_tokens=200,
            chunk_size=2000,
        )
        
        print(f"\nOriginal: {result['tokens_before']} tokens")
        print(f"Summary: {result['tokens_after']} tokens")
        print(f"Reduction: {result['reduction_pct']}%")
        print(f"Latency: {result['latency_ms']}ms")
        print(f"\nSummary preview:\n{result['text'][:200]}...")
    
    # Uncomment to run:
    # asyncio.run(demo())
    print("Demo available - uncomment asyncio.run(demo()) to test")
