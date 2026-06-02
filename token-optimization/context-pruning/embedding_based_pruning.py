"""
Embedding-based pruning: Semantic deduplication and clustering.

Removes semantically similar/duplicate documents to reduce redundancy.
Useful when retrieval returns many similar documents.

Performance:
- Reduction: 40-60%
- Latency: 100-300ms
- Quality: Medium (may remove useful variations)
"""

import logging
from typing import Optional

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from core.llm import embed
from token_optimization.compression.token_pruning import count_tokens


logger = logging.getLogger(__name__)


async def deduplicate_by_embeddings(
    documents: list[str],
    similarity_threshold: float = 0.85,
    model: str = "text-embedding-3-small",
) -> list[str]:
    """
    Remove duplicate documents based on semantic similarity.
    
    Args:
        documents: List of documents
        similarity_threshold: Similarity above this = duplicate (0-1)
        model: Embedding model
        
    Returns:
        Deduplicated document list
        
    Example:
        >>> docs = [
        ...     "Machine learning is AI",
        ...     "ML is a subset of AI",  # Very similar
        ...     "Python is a programming language",  # Different
        ... ]
        >>> unique = await deduplicate_by_embeddings(docs, threshold=0.85)
        >>> len(unique)  # 2 (first two merged)
        2
    """
    if not documents or len(documents) <= 1:
        return documents
    
    try:
        # Embed all documents
        embeddings = await embed(documents, model=model)
        embeddings_array = np.array(embeddings)
        
        # Calculate pairwise similarities
        similarities = cosine_similarity(embeddings_array)
        
        # Track which documents to keep
        keep = [True] * len(documents)
        
        # For each document, mark later similar docs as duplicates
        for i in range(len(documents)):
            if not keep[i]:
                continue
            for j in range(i + 1, len(documents)):
                if similarities[i][j] >= similarity_threshold:
                    keep[j] = False  # Mark as duplicate
        
        # Return unique documents
        unique_docs = [doc for doc, k in zip(documents, keep) if k]
        
        tokens_before = sum(count_tokens(doc) for doc in documents)
        tokens_after = sum(count_tokens(doc) for doc in unique_docs)
        reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
        
        logger.info(
            f"Deduplicated {len(documents)} → {len(unique_docs)} documents "
            f"({tokens_before} → {tokens_after} tokens, {reduction_pct:.1f}% reduction)"
        )
        
        return unique_docs
        
    except Exception as e:
        logger.error(f"Deduplication failed: {e}")
        return documents  # Return original on error


async def cluster_and_sample(
    documents: list[str],
    num_clusters: int = 5,
    samples_per_cluster: int = 1,
    model: str = "text-embedding-3-small",
) -> list[str]:
    """
    Cluster documents and sample from each cluster.
    
    Useful when you have many similar documents and want diverse coverage.
    
    Args:
        documents: List of documents
        num_clusters: Number of clusters to create
        samples_per_cluster: Documents to keep per cluster
        model: Embedding model
        
    Returns:
        Sampled documents (diverse set)
        
    Example:
        >>> docs = get_100_similar_documents()
        >>> diverse = await cluster_and_sample(docs, num_clusters=5, samples_per_cluster=2)
        >>> # Returns 10 diverse documents covering 5 topics
    """
    if not documents or len(documents) <= num_clusters:
        return documents
    
    try:
        # Embed documents
        embeddings = await embed(documents, model=model)
        embeddings_array = np.array(embeddings)
        
        # Cluster
        clustering = AgglomerativeClustering(
            n_clusters=min(num_clusters, len(documents)),
            metric='cosine',
            linkage='average',
        )
        labels = clustering.fit_predict(embeddings_array)
        
        # Sample from each cluster
        sampled = []
        for cluster_id in range(num_clusters):
            cluster_docs = [doc for doc, label in zip(documents, labels) if label == cluster_id]
            
            if cluster_docs:
                # Take up to samples_per_cluster from this cluster
                sampled.extend(cluster_docs[:samples_per_cluster])
        
        tokens_before = sum(count_tokens(doc) for doc in documents)
        tokens_after = sum(count_tokens(doc) for doc in sampled)
        reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
        
        logger.info(
            f"Clustered {len(documents)} docs into {num_clusters} clusters, "
            f"sampled {len(sampled)} ({reduction_pct:.1f}% reduction)"
        )
        
        return sampled
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return documents[:num_clusters * samples_per_cluster]  # Fallback


async def mmr_pruning(
    query: str,
    documents: list[str],
    top_k: int = 5,
    lambda_param: float = 0.5,
    model: str = "text-embedding-3-small",
) -> list[str]:
    """
    Maximal Marginal Relevance: Balance relevance and diversity.
    
    Selects documents that are relevant to query but different from each other.
    
    Args:
        query: User query
        documents: Document list
        top_k: Number of documents to select
        lambda_param: Tradeoff between relevance and diversity (0=diversity, 1=relevance)
        model: Embedding model
        
    Returns:
        Top-k documents balancing relevance and diversity
        
    Example:
        >>> # Get diverse documents about "AI"
        >>> docs = await mmr_pruning(
        ...     query="artificial intelligence applications",
        ...     documents=all_docs,
        ...     top_k=5,
        ...     lambda_param=0.5,  # Equal weight to relevance and diversity
        ... )
    """
    if not documents or len(documents) <= top_k:
        return documents[:top_k]
    
    try:
        # Embed query and documents
        all_texts = [query] + documents
        embeddings = await embed(all_texts, model=model)
        
        query_embedding = np.array(embeddings[0]).reshape(1, -1)
        doc_embeddings = np.array(embeddings[1:])
        
        # Calculate relevance scores (similarity to query)
        relevance_scores = cosine_similarity(query_embedding, doc_embeddings)[0]
        
        # Initialize
        selected_indices = []
        remaining_indices = list(range(len(documents)))
        
        # Greedily select documents
        for _ in range(min(top_k, len(documents))):
            if not remaining_indices:
                break
            
            mmr_scores = []
            for idx in remaining_indices:
                # Relevance component
                relevance = relevance_scores[idx]
                
                # Diversity component (max similarity to already selected)
                if selected_indices:
                    selected_embeddings = doc_embeddings[selected_indices]
                    current_embedding = doc_embeddings[idx].reshape(1, -1)
                    similarities = cosine_similarity(current_embedding, selected_embeddings)[0]
                    max_sim = similarities.max()
                else:
                    max_sim = 0
                
                # MMR score
                mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                mmr_scores.append((idx, mmr))
            
            # Select document with highest MMR score
            best_idx, _ = max(mmr_scores, key=lambda x: x[1])
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        result = [documents[i] for i in selected_indices]
        
        tokens_before = sum(count_tokens(doc) for doc in documents)
        tokens_after = sum(count_tokens(doc) for doc in result)
        reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
        
        logger.info(
            f"MMR pruning: {len(documents)} → {len(result)} documents "
            f"({reduction_pct:.1f}% reduction, λ={lambda_param})"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"MMR pruning failed: {e}")
        return documents[:top_k]


async def hierarchical_pruning(
    documents: list[str],
    target_count: int = 10,
    dedup_threshold: float = 0.85,
    model: str = "text-embedding-3-small",
) -> list[str]:
    """
    Multi-stage pruning: deduplicate, then cluster, then sample.
    
    Args:
        documents: Input documents
        target_count: Desired number of documents
        dedup_threshold: Deduplication threshold
        model: Embedding model
        
    Returns:
        Pruned document list
        
    Strategy:
        1. Deduplicate (remove exact duplicates)
        2. Cluster remaining documents
        3. Sample evenly from clusters to reach target_count
    """
    if len(documents) <= target_count:
        return documents
    
    logger.info(f"Hierarchical pruning: {len(documents)} → {target_count} documents")
    
    # Stage 1: Deduplicate
    unique_docs = await deduplicate_by_embeddings(documents, dedup_threshold, model)
    logger.info(f"After deduplication: {len(unique_docs)} documents")
    
    if len(unique_docs) <= target_count:
        return unique_docs
    
    # Stage 2: Cluster and sample
    num_clusters = max(3, target_count // 2)  # Reasonable number of clusters
    samples_per_cluster = max(1, target_count // num_clusters)
    
    result = await cluster_and_sample(unique_docs, num_clusters, samples_per_cluster, model)
    
    # Stage 3: If still too many, take top by length (longer = more info)
    if len(result) > target_count:
        result.sort(key=lambda x: len(x), reverse=True)
        result = result[:target_count]
    
    return result


# Metrics wrapper
async def prune_with_metrics(
    documents: list[str],
    method: str = "deduplicate",
    **kwargs
) -> dict:
    """
    Prune and return metrics.
    
    Args:
        documents: Input documents
        method: "deduplicate", "cluster", "mmr", or "hierarchical"
        **kwargs: Method-specific parameters
        
    Returns:
        Dict with documents and metrics
    """
    import time
    
    tokens_before = sum(count_tokens(doc) for doc in documents)
    start = time.perf_counter()
    
    if method == "deduplicate":
        result = await deduplicate_by_embeddings(documents, **kwargs)
    elif method == "cluster":
        result = await cluster_and_sample(documents, **kwargs)
    elif method == "mmr":
        result = await mmr_pruning(documents=documents, **kwargs)
    elif method == "hierarchical":
        result = await hierarchical_pruning(documents, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    latency_ms = (time.perf_counter() - start) * 1000
    tokens_after = sum(count_tokens(doc) for doc in result)
    reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0.0
    
    return {
        'documents': result,
        'tokens_before': tokens_before,
        'tokens_after': tokens_after,
        'reduction_pct': round(reduction_pct, 2),
        'latency_ms': round(latency_ms, 2),
        'num_before': len(documents),
        'num_after': len(result),
        'method': method,
    }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # Create sample documents with some duplicates
        documents = [
            "Machine learning is a subset of artificial intelligence.",
            "ML is a branch of AI that focuses on learning from data.",  # Similar to first
            "Python is a high-level programming language.",
            "JavaScript is used for web development.",
            "Deep learning uses neural networks with many layers.",
            "Python is known for its simplicity and readability.",  # Similar to third
            "Natural language processing enables language understanding.",
            "Java is used for enterprise applications.",
        ]
        
        print("Embedding-based Pruning Demo\n" + "="*60)
        
        result = await prune_with_metrics(
            documents,
            method="deduplicate",
            similarity_threshold=0.80,
        )
        
        print(f"\nMethod: {result['method']}")
        print(f"Documents: {result['num_before']} → {result['num_after']}")
        print(f"Tokens: {result['tokens_before']} → {result['tokens_after']} ({result['reduction_pct']}% reduction)")
        print(f"Latency: {result['latency_ms']}ms")
    
    # Uncomment to run:
    # asyncio.run(demo())
    print("Demo available - uncomment asyncio.run(demo()) to test")
