"""
Context Pruning: Keep only relevant content to fit within context limits.

This script demonstrates:
1. Keyword-based filtering
2. Embedding-based similarity pruning
3. Extractive summarization
4. Cost/quality tradeoffs

Run: python context_pruning.py
"""

import asyncio
import tiktoken
import re
from typing import List, Dict, Tuple
from collections import Counter

from core.llm import chat, embed
from core.config import get_settings


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    
    return len(enc.encode(text))


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting (can be improved with NLTK)
    sentences = re.split(r'[.!?]\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def keyword_filter(
    text: str,
    keywords: List[str],
    context_words: int = 50,
) -> str:
    """
    Filter text to keep only sentences containing keywords.
    
    Args:
        text: Input text
        keywords: Keywords to search for
        context_words: Number of words to keep around keyword
        
    Returns:
        Filtered text
    """
    sentences = split_into_sentences(text)
    keywords_lower = [k.lower() for k in keywords]
    
    # Find sentences containing keywords
    relevant_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in keywords_lower):
            relevant_sentences.append(sentence)
    
    return ". ".join(relevant_sentences) + "." if relevant_sentences else ""


def extractive_summarization(
    text: str,
    num_sentences: int = 5,
) -> str:
    """
    Extract most important sentences based on word frequency.
    
    Args:
        text: Input text
        num_sentences: Number of sentences to extract
        
    Returns:
        Extracted summary
    """
    sentences = split_into_sentences(text)
    
    if len(sentences) <= num_sentences:
        return text
    
    # Calculate word frequencies
    words = re.findall(r'\w+', text.lower())
    word_freq = Counter(words)
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    for stop in stop_words:
        word_freq.pop(stop, None)
    
    # Score sentences by sum of word frequencies
    sentence_scores = []
    for sentence in sentences:
        words_in_sentence = re.findall(r'\w+', sentence.lower())
        score = sum(word_freq.get(word, 0) for word in words_in_sentence)
        sentence_scores.append((sentence, score))
    
    # Sort by score and take top N
    top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:num_sentences]
    
    # Maintain original order
    top_text = [s for s, score in top_sentences]
    original_order = [s for s in sentences if s in top_text]
    
    return ". ".join(original_order[:num_sentences]) + "."


async def similarity_based_pruning(
    text: str,
    query: str,
    max_tokens: int = 5000,
) -> str:
    """
    Prune text to keep sentences most similar to query.
    
    Args:
        text: Input text
        query: Query/question to match against
        max_tokens: Maximum tokens to keep
        
    Returns:
        Pruned text
    """
    sentences = split_into_sentences(text)
    
    if count_tokens(text) <= max_tokens:
        return text
    
    try:
        # Embed query and sentences
        all_texts = [query] + sentences
        embeddings = await embed(all_texts)
        
        query_embedding = embeddings[0]
        sentence_embeddings = embeddings[1:]
        
        # Calculate cosine similarity
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot_product = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(y * y for y in b) ** 0.5
            return dot_product / (norm_a * norm_b) if norm_a * norm_b > 0 else 0
        
        # Rank sentences by similarity
        scored_sentences = [
            (sentence, cosine_similarity(query_embedding, sent_emb))
            for sentence, sent_emb in zip(sentences, sentence_embeddings)
        ]
        
        # Sort by similarity (descending)
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Keep sentences until max_tokens
        pruned = []
        current_tokens = 0
        
        for sentence, score in scored_sentences:
            sentence_tokens = count_tokens(sentence)
            if current_tokens + sentence_tokens <= max_tokens:
                pruned.append(sentence)
                current_tokens += sentence_tokens
            else:
                break
        
        # Maintain original order
        original_order = [s for s in sentences if s in pruned]
        
        return ". ".join(original_order) + "."
    
    except Exception as e:
        print(f"Error in similarity pruning: {e}")
        # Fallback to extractive summarization
        return extractive_summarization(text, num_sentences=10)


def prune_to_budget(
    text: str,
    max_tokens: int,
    method: str = "truncate",
) -> str:
    """
    Prune text to fit within token budget.
    
    Args:
        text: Input text
        max_tokens: Maximum tokens allowed
        method: Pruning method (truncate, extractive)
        
    Returns:
        Pruned text
    """
    current_tokens = count_tokens(text)
    
    if current_tokens <= max_tokens:
        return text
    
    if method == "truncate":
        # Simple truncation
        try:
            enc = tiktoken.encoding_for_model("gpt-4")
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        
        tokens = enc.encode(text)
        truncated_tokens = tokens[:max_tokens]
        return enc.decode(truncated_tokens) + "... [truncated]"
    
    elif method == "extractive":
        # Extractive summarization
        # Estimate number of sentences needed
        avg_tokens_per_sentence = current_tokens / len(split_into_sentences(text))
        target_sentences = int(max_tokens / avg_tokens_per_sentence)
        
        return extractive_summarization(text, num_sentences=target_sentences)
    
    else:
        # Default to truncate
        return prune_to_budget(text, max_tokens, method="truncate")


async def demo_keyword_filtering():
    """Demo: Keyword-based filtering."""
    print("="*90)
    print("DEMO 1: Keyword-Based Filtering")
    print("="*90)
    
    document = """
    The company reported strong quarterly earnings. Revenue increased by 25%
    year-over-year, reaching $500 million. The CEO expressed optimism about
    future growth prospects. The weather was sunny during the board meeting.
    Operating expenses remained flat at $300 million. The office cafeteria
    introduced new menu items. Profit margins improved to 40%, up from 35%
    last quarter. Employee satisfaction surveys showed positive results.
    """
    
    print(f"\nOriginal document ({count_tokens(document)} tokens):")
    print(document[:200] + "...")
    
    keywords = ["revenue", "profit", "earnings", "expenses"]
    
    filtered = keyword_filter(document, keywords)
    
    print(f"\nFiltered (keywords: {keywords}):")
    print(f"Tokens: {count_tokens(filtered)} (reduced by {count_tokens(document) - count_tokens(filtered)})")
    print(filtered)


async def demo_extractive_summarization():
    """Demo: Extractive summarization."""
    print("\n" + "="*90)
    print("DEMO 2: Extractive Summarization")
    print("="*90)
    
    document = """
    Artificial intelligence is transforming industries worldwide. Machine learning
    algorithms can now process vast amounts of data in seconds. Companies are
    investing heavily in AI research and development. The technology has applications
    in healthcare, finance, and transportation. Some experts worry about job
    displacement due to automation. Others see AI as a tool to augment human
    capabilities. Ethical considerations around AI deployment are increasingly
    important. Regulatory frameworks are being developed to govern AI use.
    Privacy concerns remain a significant challenge. The future of AI depends
    on responsible development and deployment practices.
    """ * 3
    
    print(f"\nOriginal document: {count_tokens(document)} tokens")
    
    # Extract top 5 sentences
    summary = extractive_summarization(document, num_sentences=5)
    
    print(f"\nExtractive summary (5 sentences): {count_tokens(summary)} tokens")
    print(summary)
    
    print(f"\nReduction: {count_tokens(document)} → {count_tokens(summary)} tokens")
    print(f"Compression ratio: {count_tokens(summary) / count_tokens(document) * 100:.1f}%")


async def demo_similarity_pruning():
    """Demo: Similarity-based pruning."""
    print("\n" + "="*90)
    print("DEMO 3: Similarity-Based Pruning")
    print("="*90)
    
    settings = get_settings()
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        print("\n⚠️  Skipping similarity pruning (no API keys found)")
        return
    
    document = """
    The product launch was successful. Sales exceeded expectations in the first week.
    Marketing campaigns reached millions of users. Customer feedback has been
    overwhelmingly positive. The new features address long-standing user requests.
    Technical support teams are well-prepared. The weather forecast predicts rain.
    Integration with existing systems went smoothly. Performance benchmarks show
    significant improvements. Competitors have not yet matched our capabilities.
    The office renovations are nearly complete. Future roadmap includes mobile apps.
    """
    
    query = "What was the customer response to the product launch?"
    
    print(f"\nOriginal document: {count_tokens(document)} tokens")
    print(f"Query: '{query}'")
    
    pruned = await similarity_based_pruning(document, query, max_tokens=100)
    
    print(f"\nPruned document: {count_tokens(pruned)} tokens")
    print(pruned)


async def demo_cost_comparison():
    """Demo: Cost comparison of pruning strategies."""
    print("\n" + "="*90)
    print("DEMO 4: Cost Comparison")
    print("="*90)
    
    # Simulate a large document
    doc_tokens = 50_000
    
    # Model pricing (GPT-4o-mini)
    input_price_per_1m = 0.15
    output_price_per_1m = 0.60
    output_tokens = 500
    
    # Scenario 1: No pruning (fails if > context limit)
    cost_no_pruning = (
        (doc_tokens / 1_000_000) * input_price_per_1m +
        (output_tokens / 1_000_000) * output_price_per_1m
    )
    
    # Scenario 2: Pruned to 10K tokens
    pruned_tokens = 10_000
    cost_pruned = (
        (pruned_tokens / 1_000_000) * input_price_per_1m +
        (output_tokens / 1_000_000) * output_price_per_1m
    )
    
    print(f"\nDocument: {doc_tokens:,} tokens")
    print(f"\nScenario 1: No pruning")
    print(f"  Input tokens: {doc_tokens:,}")
    print(f"  Cost: ${cost_no_pruning:.6f}")
    
    print(f"\nScenario 2: Pruned to {pruned_tokens:,} tokens")
    print(f"  Input tokens: {pruned_tokens:,}")
    print(f"  Cost: ${cost_pruned:.6f}")
    print(f"  Savings: ${cost_no_pruning - cost_pruned:.6f} ({(1 - cost_pruned/cost_no_pruning)*100:.1f}%)")


async def demo_pruning_methods():
    """Demo: Compare different pruning methods."""
    print("\n" + "="*90)
    print("DEMO 5: Pruning Methods Comparison")
    print("="*90)
    
    document = """
    Climate change is affecting global weather patterns. Scientists have observed
    rising temperatures over the past century. Greenhouse gas emissions are the
    primary cause. Many countries have committed to reducing emissions. Renewable
    energy adoption is increasing worldwide. Solar and wind power are becoming
    more cost-effective. Electric vehicles are gaining market share. Deforestation
    contributes to carbon dioxide levels. Ocean acidification threatens marine life.
    Policy changes are needed to address the crisis. Individual actions also matter.
    """ * 5
    
    max_tokens = 200
    
    print(f"\nOriginal: {count_tokens(document)} tokens")
    print(f"Target: {max_tokens} tokens\n")
    
    # Method 1: Truncation
    truncated = prune_to_budget(document, max_tokens, method="truncate")
    print(f"Truncation method: {count_tokens(truncated)} tokens")
    print(f"  Preview: {truncated[:150]}...")
    
    # Method 2: Extractive
    extractive = prune_to_budget(document, max_tokens, method="extractive")
    print(f"\nExtractive method: {count_tokens(extractive)} tokens")
    print(f"  Preview: {extractive[:150]}...")
    
    print("\nComparison:")
    print("  • Truncation: Fast but loses end of document")
    print("  • Extractive: Preserves key sentences throughout")


async def main():
    """Run all context pruning demos."""
    print("="*90)
    print("✂️  CONTEXT PRUNING DEMO")
    print("="*90)
    
    await demo_keyword_filtering()
    await demo_extractive_summarization()
    await demo_similarity_pruning()
    await demo_cost_comparison()
    await demo_pruning_methods()
    
    print("\n" + "="*90)
    print("✅ Demo complete!")
    print("="*90)
    print("\nKey takeaways:")
    print("  • Pruning reduces costs by lowering input tokens")
    print("  • Keyword filtering keeps relevant sections")
    print("  • Extractive summarization preserves important sentences")
    print("  • Similarity-based pruning matches content to query")
    print("  • Always measure quality vs cost tradeoff")


if __name__ == "__main__":
    asyncio.run(main())
