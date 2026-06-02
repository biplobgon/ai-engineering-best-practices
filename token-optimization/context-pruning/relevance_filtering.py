"""
Relevance filtering: Keep only documents relevant to the query.

This is the most effective token reduction technique for RAG systems.
Typical: 20 retrieved docs → 3-5 most relevant = 80% reduction.

Performance:
- Reduction: 60-80%
- Latency: 50-200ms (embedding + scoring)
- Quality: High (keeps best matches)
"""

import asyncio
import logging
from typing import Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from core.llm import embed
from token_optimization.compression.token_pruning import count_tokens


logger = logging.getLogger(__name__)


async def filter_by_similarity(
    query: str,
    documents: list[str],
    top_k: int = 5,
    model: str = "text-embedding-3-small",
    threshold: Optional[float] = None,
) -> list[str]:
    """
    Filter documents by cosine similarity to query.
    
    Args:
        query: User query
        documents: List of document strings
        top_k: Number of documents to keep
        model: Embedding model
        threshold: If specified, also filter by minimum similarity score
        
    Returns:
        Top-k most relevant documents (sorted by relevance)
        
    Example:
        >>> docs = ["Doc about AI", "Doc about cooking", "Doc about ML"]
        >>> relevant = await filter_by_similarity("machine learning", docs, top_k=2)
        >>> # Returns: ["Doc about ML", "Doc about AI"]
    """
    if not documents:
        return []
    
    if len(documents) <= top_k:
        return documents
    
    # Embed query and documents
    all_texts = [query] + documents
    
    try:
        embeddings = await embed(all_texts, model=model)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        # Fallback: return first top_k
        return documents[:top_k]
    
    query_embedding = np.array(embeddings[0]).reshape(1, -1)
    doc_embeddings = np.array(embeddings[1:])
    
    # Calculate similarities
    similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
    
    # Sort by similarity (descending)
    sorted_indices = np.argsort(similarities)[::-1]
    
    # Apply threshold if specified
    if threshold is not None:
        sorted_indices = [i for i in sorted_indices if similarities[i] >= threshold]
    
    # Take top-k
    top_indices = sorted_indices[:top_k]
    
    # Return documents in relevance order
    result = [documents[i] for i in top_indices]
    
    # Log metrics
    tokens_before = sum(count_tokens(doc) for doc in documents)
    tokens_after = sum(count_tokens(doc) for doc in result)
    reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
    
    logger.info(
        f"Filtered {len(documents)} → {len(result)} documents "
        f"({tokens_before} → {tokens_after} tokens, {reduction_pct:.1f}% reduction)"
    )
    
    return result


async def filter_with_scores(
    query: str,
    documents: list[str],
    top_k: int = 5,
    model: str = "text-embedding-3-small",
) -> list[tuple[str, float]]:
    """
    Same as filter_by_similarity but returns (document, score) tuples.
    
    Returns:
        List of (document, similarity_score) tuples, sorted by score
    """
    if not documents:
        return []
    
    all_texts = [query] + documents
    embeddings = await embed(all_texts, model=model)
    
    query_embedding = np.array(embeddings[0]).reshape(1, -1)
    doc_embeddings = np.array(embeddings[1:])
    
    similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
    
    # Create (doc, score) pairs
    doc_scores = list(zip(documents, similarities))
    
    # Sort by score (descending)
    doc_scores.sort(key=lambda x: x[1], reverse=True)
    
    return doc_scores[:top_k]


async def batch_filter(
    queries: list[str],
    document_sets: list[list[str]],
    top_k: int = 5,
    model: str = "text-embedding-3-small",
) -> list[list[str]]:
    """
    Filter multiple query-document pairs in parallel.
    
    Args:
        queries: List of queries
        document_sets: List of document lists (one per query)
        top_k: Documents to keep per query
        model: Embedding model
        
    Returns:
        List of filtered document lists
    """
    tasks = [
        filter_by_similarity(query, docs, top_k, model)
        for query, docs in zip(queries, document_sets)
    ]
    
    return await asyncio.gather(*tasks)


def keyword_score(query: str, document: str) -> float:
    """
    Simple keyword overlap score (BM25-like, simplified).
    
    Args:
        query: Query string
        document: Document string
        
    Returns:
        Score between 0 and 1
    """
    # Normalize
    query_terms = set(query.lower().split())
    doc_terms = set(document.lower().split())
    
    if not query_terms:
        return 0.0
    
    # Jaccard similarity
    intersection = query_terms & doc_terms
    union = query_terms | doc_terms
    
    return len(intersection) / len(union) if union else 0.0


async def hybrid_filter(
    query: str,
    documents: list[str],
    top_k: int = 5,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
    model: str = "text-embedding-3-small",
) -> list[str]:
    """
    Hybrid filtering: combine vector similarity + keyword matching.
    
    Args:
        query: User query
        documents: Document list
        top_k: Documents to keep
        vector_weight: Weight for vector similarity (0-1)
        keyword_weight: Weight for keyword matching (0-1)
        model: Embedding model
        
    Returns:
        Top-k documents by hybrid score
        
    Example:
        >>> # Boost documents with exact keyword matches
        >>> docs = await hybrid_filter(
        ...     query="Python programming",
        ...     documents=all_docs,
        ...     vector_weight=0.6,
        ...     keyword_weight=0.4,  # Higher weight for keyword match
        ... )
    """
    if not documents:
        return []
    
    # Get vector scores
    doc_scores_vector = await filter_with_scores(query, documents, top_k=len(documents), model=model)
    
    # Get keyword scores
    keyword_scores = [keyword_score(query, doc) for doc in documents]
    
    # Normalize vector scores to 0-1
    vector_scores = [score for _, score in doc_scores_vector]
    max_vector = max(vector_scores) if vector_scores else 1.0
    vector_scores_norm = [s / max_vector for s in vector_scores]
    
    # Combine scores
    hybrid_scores = [
        vector_weight * v + keyword_weight * k
        for v, k in zip(vector_scores_norm, keyword_scores)
    ]
    
    # Sort by hybrid score
    doc_score_pairs = list(zip(documents, hybrid_scores))
    doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
    
    # Return top-k
    return [doc for doc, _ in doc_score_pairs[:top_k]]


async def filter_with_metadata(
    query: str,
    documents: list[dict],
    top_k: int = 5,
    text_field: str = "content",
    boost_fields: Optional[dict[str, float]] = None,
    model: str = "text-embedding-3-small",
) -> list[dict]:
    """
    Filter documents with metadata boosting.
    
    Args:
        query: User query
        documents: List of dicts with metadata (must have text_field)
        top_k: Documents to keep
        text_field: Key containing document text
        boost_fields: Optional field boosts (e.g., {"title": 1.5, "summary": 1.2})
        model: Embedding model
        
    Returns:
        Top-k documents with metadata preserved
        
    Example:
        >>> docs = [
        ...     {"content": "...", "title": "Important Doc", "date": "2024-01-01"},
        ...     {"content": "...", "title": "Other Doc", "date": "2024-01-02"},
        ... ]
        >>> filtered = await filter_with_metadata(
        ...     query="important information",
        ...     documents=docs,
        ...     boost_fields={"title": 1.5},  # Boost title matches
        ... )
    """
    if not documents:
        return []
    
    # Extract text for embedding
    texts = [doc.get(text_field, "") for doc in documents]
    
    # Get base scores
    doc_scores = await filter_with_scores(query, texts, top_k=len(documents), model=model)
    
    # Apply metadata boosts
    if boost_fields:
        boosted_scores = []
        for (text, base_score), doc in zip(doc_scores, documents):
            boost = 1.0
            for field, weight in boost_fields.items():
                if field in doc and query.lower() in str(doc[field]).lower():
                    boost *= weight
            boosted_scores.append((doc, base_score * boost))
    else:
        boosted_scores = [(doc, score) for (_, score), doc in zip(doc_scores, documents)]
    
    # Sort by boosted score
    boosted_scores.sort(key=lambda x: x[1], reverse=True)
    
    return [doc for doc, _ in boosted_scores[:top_k]]


# Metrics wrapper
async def filter_with_metrics(
    query: str,
    documents: list[str],
    top_k: int = 5,
    **kwargs
) -> dict:
    """
    Filter and return detailed metrics.
    
    Returns:
        Dict with:
        - documents: Filtered documents
        - tokens_before: Total tokens before
        - tokens_after: Total tokens after
        - reduction_pct: Percentage reduction
        - latency_ms: Time taken
        - scores: Similarity scores
    """
    import time
    
    tokens_before = sum(count_tokens(doc) for doc in documents)
    start = time.perf_counter()
    
    doc_scores = await filter_with_scores(query, documents, top_k, **kwargs)
    
    latency_ms = (time.perf_counter() - start) * 1000
    
    filtered_docs = [doc for doc, _ in doc_scores]
    scores = [float(score) for _, score in doc_scores]
    tokens_after = sum(count_tokens(doc) for doc in filtered_docs)
    reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
    
    return {
        'documents': filtered_docs,
        'tokens_before': tokens_before,
        'tokens_after': tokens_after,
        'reduction_pct': round(reduction_pct, 2),
        'latency_ms': round(latency_ms, 2),
        'scores': scores,
        'num_filtered': len(documents),
        'num_kept': len(filtered_docs),
    }


# Example usage
if __name__ == "__main__":
    async def demo():
        # Sample documents
        documents = [
            "Machine learning is a subset of artificial intelligence focused on algorithms that improve through experience.",
            "Python is a high-level programming language known for its simplicity and readability.",
            "Deep learning uses neural networks with multiple layers to model complex patterns in data.",
            "JavaScript is primarily used for web development and runs in browsers.",
            "Natural language processing enables computers to understand and generate human language.",
            "Java is an object-oriented programming language used for enterprise applications.",
            "Computer vision allows machines to interpret and understand visual information from the world.",
            "C++ is known for its performance and is used in system programming and game development.",
        ]
        
        query = "What is machine learning?"
        
        print("Relevance Filtering Demo\n" + "="*60)
        print(f"Query: {query}")
        print(f"Documents: {len(documents)}")
        
        result = await filter_with_metrics(query, documents, top_k=3)
        
        print(f"\nTokens: {result['tokens_before']} → {result['tokens_after']} ({result['reduction_pct']}% reduction)")
        print(f"Latency: {result['latency_ms']}ms")
        print(f"\nTop 3 documents:")
        for i, (doc, score) in enumerate(zip(result['documents'], result['scores']), 1):
            print(f"\n{i}. Score: {score:.3f}")
            print(f"   {doc[:80]}...")
    
    # Uncomment to run:
    # asyncio.run(demo())
    print("Demo available - uncomment asyncio.run(demo()) to test")
