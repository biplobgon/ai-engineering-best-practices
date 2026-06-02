"""
Similarity Search: Build a simple semantic search engine.

This script demonstrates:
1. Building an in-memory search index
2. Adding documents with embeddings
3. Querying for similar documents
4. Comparing with keyword search

Run: python similarity_search.py
"""

import asyncio
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from core.llm import embed
from core.config import get_settings


@dataclass
class Document:
    """Represents a document with metadata."""
    id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict] = None


class SemanticSearchEngine:
    """Simple in-memory semantic search engine."""
    
    def __init__(self):
        """Initialize empty search engine."""
        self.documents: List[Document] = []
        self.indexed = False
    
    async def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        """
        Add documents to the search engine.
        
        Args:
            texts: List of document texts
            metadatas: Optional metadata for each document
        """
        # Generate embeddings in batch
        print(f"Embedding {len(texts)} documents...")
        embeddings = await embed(texts)
        
        # Create document objects
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            
            doc = Document(
                id=f"doc_{len(self.documents) + i}",
                text=text,
                embedding=embedding,
                metadata=metadata,
            )
            self.documents.append(doc)
        
        self.indexed = True
        print(f"Indexed {len(texts)} documents (total: {len(self.documents)})")
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.indexed:
            raise ValueError("No documents indexed. Call add_documents() first.")
        
        # Embed query
        query_embedding = (await embed([query]))[0]
        
        # Calculate similarities
        results = []
        for doc in self.documents:
            similarity = self.cosine_similarity(query_embedding, doc.embedding)
            
            if similarity >= threshold:
                results.append((doc, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Document]:
        """
        Simple keyword search (for comparison).
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of matching documents
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score documents by keyword overlap
        scored_docs = []
        for doc in self.documents:
            doc_words = set(doc.text.lower().split())
            overlap = len(query_words & doc_words)
            
            if overlap > 0:
                scored_docs.append((doc, overlap))
        
        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs[:top_k]]


async def demo_basic_search():
    """Demo: Basic semantic search."""
    print("="*90)
    print("DEMO 1: Basic Semantic Search")
    print("="*90)
    
    # Create search engine
    engine = SemanticSearchEngine()
    
    # Sample documents
    documents = [
        "Python is a versatile programming language used for web development",
        "Machine learning algorithms can predict outcomes from data",
        "The Great Wall of China is a historical landmark",
        "Deep learning uses neural networks with multiple layers",
        "Italian pasta dishes are popular worldwide",
        "Natural language processing enables computers to understand text",
        "The Amazon rainforest is home to diverse wildlife",
        "Artificial intelligence is transforming industries",
    ]
    
    print(f"\nIndexing {len(documents)} documents...")
    await engine.add_documents(documents)
    
    # Search query
    query = "Tell me about AI and machine learning"
    print(f"\nQuery: '{query}'")
    
    results = await engine.search(query, top_k=5)
    
    print(f"\nTop 5 results:")
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n  {i}. Similarity: {score:.4f}")
        print(f"     {doc.text}")


async def demo_threshold_filtering():
    """Demo: Filtering results by similarity threshold."""
    print("\n" + "="*90)
    print("DEMO 2: Similarity Threshold Filtering")
    print("="*90)
    
    engine = SemanticSearchEngine()
    
    documents = [
        "Python programming tutorials for beginners",
        "Advanced Python techniques for experts",
        "JavaScript web development guide",
        "Cooking Italian recipes at home",
        "Python data science libraries",
    ]
    
    await engine.add_documents(documents)
    
    query = "Learning Python programming"
    
    # Different thresholds
    thresholds = [0.0, 0.5, 0.7, 0.9]
    
    print(f"\nQuery: '{query}'")
    
    for threshold in thresholds:
        results = await engine.search(query, top_k=10, threshold=threshold)
        
        print(f"\nThreshold: {threshold:.1f}")
        print(f"Results: {len(results)}")
        
        for doc, score in results:
            print(f"  - {score:.4f}: {doc.text[:60]}...")


async def demo_semantic_vs_keyword():
    """Demo: Compare semantic search with keyword search."""
    print("\n" + "="*90)
    print("DEMO 3: Semantic vs Keyword Search")
    print("="*90)
    
    engine = SemanticSearchEngine()
    
    documents = [
        "Artificial intelligence revolutionizes healthcare diagnostics",
        "Machine learning models predict customer behavior",
        "Neural networks power modern AI systems",
        "The history of ancient Rome is fascinating",
        "Deep learning techniques for image recognition",
        "Traditional Italian cooking methods",
    ]
    
    await engine.add_documents(documents)
    
    query = "AI and machine learning applications"
    
    print(f"\nQuery: '{query}'")
    
    # Keyword search
    print(f"\n{'='*90}")
    print("Keyword Search Results:")
    print(f"{'='*90}")
    
    keyword_results = engine.keyword_search(query, top_k=3)
    
    if keyword_results:
        for i, doc in enumerate(keyword_results, 1):
            print(f"\n  {i}. {doc.text}")
    else:
        print("\n  No keyword matches found!")
    
    # Semantic search
    print(f"\n{'='*90}")
    print("Semantic Search Results:")
    print(f"{'='*90}")
    
    semantic_results = await engine.search(query, top_k=3)
    
    for i, (doc, score) in enumerate(semantic_results, 1):
        print(f"\n  {i}. Similarity: {score:.4f}")
        print(f"     {doc.text}")
    
    print("\nAnalysis:")
    print("  • Keyword search: Finds exact word matches only")
    print("  • Semantic search: Finds conceptually related content")
    print("  • Semantic search captures meaning, not just keywords")


async def demo_metadata_filtering():
    """Demo: Combine semantic search with metadata filtering."""
    print("\n" + "="*90)
    print("DEMO 4: Search with Metadata Filtering")
    print("="*90)
    
    documents = [
        "Python for data science and analysis",
        "JavaScript framework comparisons",
        "Advanced Python web development",
        "Python machine learning basics",
        "Java enterprise applications",
    ]
    
    metadatas = [
        {"category": "data_science", "difficulty": "intermediate"},
        {"category": "web_dev", "difficulty": "beginner"},
        {"category": "web_dev", "difficulty": "advanced"},
        {"category": "data_science", "difficulty": "beginner"},
        {"category": "enterprise", "difficulty": "advanced"},
    ]
    
    engine = SemanticSearchEngine()
    await engine.add_documents(documents, metadatas)
    
    query = "learning Python"
    
    print(f"\nQuery: '{query}'")
    
    # Search all
    print(f"\nAll results:")
    results = await engine.search(query, top_k=5)
    for doc, score in results:
        print(f"  {score:.4f}: {doc.text} [{doc.metadata}]")
    
    # Filter by category
    print(f"\nFiltered (category='data_science'):")
    results = await engine.search(query, top_k=5)
    filtered = [(doc, score) for doc, score in results if doc.metadata.get("category") == "data_science"]
    for doc, score in filtered:
        print(f"  {score:.4f}: {doc.text} [{doc.metadata}]")


async def demo_real_world_faq():
    """Demo: Real-world FAQ search."""
    print("\n" + "="*90)
    print("DEMO 5: FAQ Search System")
    print("="*90)
    
    # FAQ database
    faqs = [
        "How do I reset my password? Click 'Forgot Password' on the login page.",
        "What payment methods do you accept? We accept credit cards, PayPal, and bank transfers.",
        "How long does shipping take? Standard shipping takes 5-7 business days.",
        "Can I return a product? Yes, within 30 days with original receipt.",
        "Do you offer international shipping? Yes, we ship to over 100 countries.",
        "How do I track my order? Use the tracking number sent to your email.",
        "What is your refund policy? Full refunds within 30 days of purchase.",
        "How do I contact customer support? Email support@example.com or call 1-800-EXAMPLE.",
    ]
    
    engine = SemanticSearchEngine()
    await engine.add_documents(faqs)
    
    # Customer queries
    queries = [
        "I forgot my login credentials",
        "What are my payment options?",
        "How do I find my package?",
    ]
    
    print(f"\nFAQ Search System ({len(faqs)} FAQs indexed)")
    
    for query in queries:
        print(f"\n{'='*90}")
        print(f"Customer question: '{query}'")
        print(f"{'='*90}")
        
        results = await engine.search(query, top_k=2)
        
        print("\nRelevant FAQs:")
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n  {i}. Confidence: {score:.4f}")
            print(f"     {doc.text}")


async def demo_performance_metrics():
    """Demo: Search performance metrics."""
    print("\n" + "="*90)
    print("DEMO 6: Search Performance")
    print("="*90)
    
    import time
    
    # Create different sized corpora
    sizes = [10, 50, 100]
    
    print("\nSearch latency by corpus size:")
    print(f"\n{'Corpus Size':>15} {'Index Time':>15} {'Search Time':>15} {'Total Time':>15}")
    print("-" * 65)
    
    for size in sizes:
        # Generate documents
        documents = [f"Document number {i} about various topics" for i in range(size)]
        
        # Measure indexing time
        engine = SemanticSearchEngine()
        start = time.time()
        await engine.add_documents(documents)
        index_time = time.time() - start
        
        # Measure search time
        start = time.time()
        await engine.search("find relevant information", top_k=5)
        search_time = time.time() - start
        
        total_time = index_time + search_time
        
        print(f"{size:>15} {index_time:>14.3f}s {search_time:>14.3f}s {total_time:>14.3f}s")
    
    print("\nNotes:")
    print("  • Indexing: One-time cost (can be done offline)")
    print("  • Search: Real-time (must be fast)")
    print("  • Larger corpus = slower search (use vector DB for scale)")


async def main():
    """Run all similarity search demos."""
    print("="*90)
    print("🔍 SIMILARITY SEARCH DEMO")
    print("="*90)
    
    settings = get_settings()
    
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        print("\n⚠️  Warning: No API keys found in environment.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run demos.")
        return
    
    await demo_basic_search()
    await demo_threshold_filtering()
    await demo_semantic_vs_keyword()
    await demo_metadata_filtering()
    await demo_real_world_faq()
    await demo_performance_metrics()
    
    print("\n" + "="*90)
    print("✅ Demo complete!")
    print("="*90)
    print("\nKey takeaways:")
    print("  • Semantic search finds meaning, not just keywords")
    print("  • Cosine similarity measures semantic relatedness")
    print("  • Threshold filtering controls result quality")
    print("  • Metadata adds structured filtering")
    print("  • For production: use vector databases (Pinecone, Weaviate, etc.)")
    print("\n🎓 You've completed all Fundamentals lessons!")
    print("   Next: Explore advanced topics like RAG, prompt engineering, and production deployment.")


if __name__ == "__main__":
    asyncio.run(main())
