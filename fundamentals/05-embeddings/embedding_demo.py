"""
Embedding Demo: Create and compare embeddings using core/llm.

This script demonstrates:
1. Creating embeddings with core.llm.embed()
2. Calculating cosine similarity
3. Finding similar documents
4. Comparing semantic vs keyword matching

Run: python embedding_demo.py

Note: Requires API keys set in environment or .env file.
"""

import asyncio
import math
from typing import List, Tuple, Dict

from core.llm import embed
from core.config import get_settings


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score (-1 to 1, higher = more similar)
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same dimensions")
    
    # Dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Magnitudes
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    # Cosine similarity
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Euclidean distance between two vectors."""
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same dimensions")
    
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


async def find_most_similar(
    query: str,
    documents: List[str],
    top_k: int = 3,
) -> List[Tuple[str, float]]:
    """
    Find most similar documents to query.
    
    Args:
        query: Query text
        documents: List of documents
        top_k: Number of top results to return
        
    Returns:
        List of (document, similarity_score) tuples
    """
    # Embed query and documents together (batch)
    all_texts = [query] + documents
    embeddings = await embed(all_texts)
    
    query_embedding = embeddings[0]
    doc_embeddings = embeddings[1:]
    
    # Calculate similarities
    similarities = []
    for i, doc_emb in enumerate(doc_embeddings):
        sim = cosine_similarity(query_embedding, doc_emb)
        similarities.append((documents[i], sim))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:top_k]


async def demo_basic_embeddings():
    """Demo: Create and examine basic embeddings."""
    print("="*90)
    print("DEMO 1: Basic Embeddings")
    print("="*90)
    
    texts = [
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses neural networks",
        "The weather is sunny today",
    ]
    
    print("\nEmbedding texts:")
    for i, text in enumerate(texts, 1):
        print(f"  {i}. {text}")
    
    embeddings = await embed(texts)
    
    print(f"\nGenerated {len(embeddings)} embeddings")
    print(f"Embedding dimensions: {len(embeddings[0])}")
    print(f"\nFirst embedding (first 10 values):")
    print(f"  {embeddings[0][:10]}")


async def demo_similarity_calculation():
    """Demo: Calculate similarity between texts."""
    print("\n" + "="*90)
    print("DEMO 2: Similarity Calculation")
    print("="*90)
    
    pairs = [
        ("Python programming", "Python coding"),
        ("Python programming", "Java development"),
        ("Python programming", "Cooking recipes"),
        ("Machine learning", "Artificial intelligence"),
        ("Machine learning", "Baking cookies"),
    ]
    
    print("\nCalculating similarities:\n")
    
    for text1, text2 in pairs:
        embeddings = await embed([text1, text2])
        similarity = cosine_similarity(embeddings[0], embeddings[1])
        
        # Visual indicator
        if similarity > 0.8:
            indicator = "🟢 Very similar"
        elif similarity > 0.6:
            indicator = "🟡 Similar"
        else:
            indicator = "🔴 Not similar"
        
        print(f"{indicator}")
        print(f"  '{text1}' ↔ '{text2}'")
        print(f"  Similarity: {similarity:.4f}\n")


async def demo_semantic_search():
    """Demo: Semantic search over documents."""
    print("\n" + "="*90)
    print("DEMO 3: Semantic Search")
    print("="*90)
    
    # Document corpus
    documents = [
        "Python is a high-level programming language known for its simplicity",
        "Machine learning enables computers to learn from data without explicit programming",
        "Neural networks are computing systems inspired by biological neural networks",
        "The Eiffel Tower is a famous landmark in Paris, France",
        "Deep learning is a subset of machine learning using multi-layer neural networks",
        "Italian cuisine is known for pasta, pizza, and other delicious foods",
        "Natural language processing helps computers understand human language",
        "The Great Wall of China is one of the Seven Wonders of the World",
    ]
    
    queries = [
        "How does AI learn?",
        "Tell me about famous monuments",
        "What is Python?",
    ]
    
    print(f"\nDocument corpus ({len(documents)} documents):")
    for i, doc in enumerate(documents, 1):
        print(f"  {i}. {doc[:60]}...")
    
    for query in queries:
        print(f"\n{'='*90}")
        print(f"Query: '{query}'")
        print(f"{'='*90}")
        
        results = await find_most_similar(query, documents, top_k=3)
        
        print("\nTop 3 matches:")
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n  {i}. Similarity: {score:.4f}")
            print(f"     {doc}")


async def demo_keyword_vs_semantic():
    """Demo: Keyword search vs semantic search."""
    print("\n" + "="*90)
    print("DEMO 4: Keyword vs Semantic Search")
    print("="*90)
    
    documents = [
        "Artificial intelligence and machine learning revolutionize technology",
        "AI systems can process vast amounts of information quickly",
        "Neural networks mimic the human brain's structure",
        "Dogs are loyal and friendly pets",
    ]
    
    query = "How does machine learning work?"
    
    print(f"\nQuery: '{query}'")
    print(f"\nDocuments:")
    for i, doc in enumerate(documents, 1):
        print(f"  {i}. {doc}")
    
    # Keyword search (naive)
    print(f"\n{'='*90}")
    print("Keyword Search (looking for 'machine learning'):")
    print(f"{'='*90}")
    
    keyword_matches = [
        (i+1, doc) for i, doc in enumerate(documents)
        if "machine learning" in doc.lower()
    ]
    
    if keyword_matches:
        for num, doc in keyword_matches:
            print(f"\n  Match: Document {num}")
            print(f"  {doc}")
    else:
        print("\n  No exact keyword matches found!")
    
    # Semantic search
    print(f"\n{'='*90}")
    print("Semantic Search (using embeddings):")
    print(f"{'='*90}")
    
    results = await find_most_similar(query, documents, top_k=3)
    
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n  {i}. Similarity: {score:.4f}")
        print(f"     {doc}")


async def demo_similarity_metrics():
    """Demo: Compare cosine vs Euclidean distance."""
    print("\n" + "="*90)
    print("DEMO 5: Cosine vs Euclidean Distance")
    print("="*90)
    
    texts = [
        "Machine learning",
        "Artificial intelligence",
        "Cooking pasta",
    ]
    
    print("\nComparing similarity metrics:\n")
    
    embeddings = await embed(texts)
    
    print(f"{'Pair':<50} {'Cosine':>12} {'Euclidean':>12}")
    print("-" * 80)
    
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            cosine_sim = cosine_similarity(embeddings[i], embeddings[j])
            euclidean_dist = euclidean_distance(embeddings[i], embeddings[j])
            
            pair_name = f"'{texts[i]}' ↔ '{texts[j]}'"
            print(f"{pair_name:<50} {cosine_sim:>12.4f} {euclidean_dist:>12.2f}")
    
    print("\nNote:")
    print("  • Cosine similarity: 1.0 = identical, 0 = orthogonal, -1 = opposite")
    print("  • Euclidean distance: 0 = identical, higher = more different")
    print("  • Cosine is preferred for embeddings (measures direction, not magnitude)")


async def demo_batch_efficiency():
    """Demo: Batch vs individual embedding efficiency."""
    print("\n" + "="*90)
    print("DEMO 6: Batch Embedding Efficiency")
    print("="*90)
    
    settings = get_settings()
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        print("\n⚠️  Skipping efficiency demo (no API keys found)")
        return
    
    texts = [f"Document number {i}" for i in range(10)]
    
    print(f"\nEmbedding {len(texts)} texts:")
    
    # Batch approach (recommended)
    import time
    start = time.time()
    embeddings_batch = await embed(texts)
    batch_time = time.time() - start
    
    print(f"\n  Batch approach:")
    print(f"    API calls: 1")
    print(f"    Time: {batch_time:.3f}s")
    print(f"    Embeddings: {len(embeddings_batch)}")
    
    # Individual approach (not recommended, for demo only)
    print(f"\n  Individual approach (simulated):")
    print(f"    API calls: {len(texts)}")
    print(f"    Estimated time: ~{batch_time * len(texts):.3f}s")
    print(f"\n  ⚠️  Batch approach is {len(texts)}× more efficient!")


async def main():
    """Run all embedding demos."""
    print("="*90)
    print("🔢 EMBEDDINGS DEMO")
    print("="*90)
    
    settings = get_settings()
    
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        print("\n⚠️  Warning: No API keys found in environment.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run live demos.")
        print("   Continuing with limited demonstrations...\n")
        return
    
    await demo_basic_embeddings()
    await demo_similarity_calculation()
    await demo_semantic_search()
    await demo_keyword_vs_semantic()
    await demo_similarity_metrics()
    await demo_batch_efficiency()
    
    print("\n" + "="*90)
    print("✅ Demo complete!")
    print("="*90)
    print("\nKey takeaways:")
    print("  • Embeddings capture semantic meaning as vectors")
    print("  • Cosine similarity measures semantic similarity")
    print("  • Semantic search finds related content, not just keywords")
    print("  • Batch embeddings for efficiency")
    print("  • Use cosine similarity (not Euclidean) for embeddings")
    print("\n🎉 Congratulations! You've completed the Fundamentals lessons!")


if __name__ == "__main__":
    asyncio.run(main())
