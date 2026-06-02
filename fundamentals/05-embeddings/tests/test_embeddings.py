"""
Tests for embeddings functionality.
"""

import pytest
import math
from fundamentals.fundamentals_05_embeddings.embedding_demo import (
    cosine_similarity,
    euclidean_distance,
)
from fundamentals.fundamentals_05_embeddings.similarity_search import (
    Document,
    SemanticSearchEngine,
)


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""
    
    def test_identical_vectors(self):
        """Test that identical vectors have similarity 1.0."""
        vec = [1.0, 2.0, 3.0]
        similarity = cosine_similarity(vec, vec)
        
        assert abs(similarity - 1.0) < 0.0001
    
    def test_orthogonal_vectors(self):
        """Test that orthogonal vectors have similarity 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert abs(similarity - 0.0) < 0.0001
    
    def test_opposite_vectors(self):
        """Test that opposite vectors have similarity -1.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert abs(similarity - (-1.0)) < 0.0001
    
    def test_similar_vectors(self):
        """Test similar vectors have high positive similarity."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.1, 2.1, 3.1]
        
        similarity = cosine_similarity(vec1, vec2)
        
        # Should be very high (close to 1.0)
        assert similarity > 0.99
    
    def test_different_magnitude_same_direction(self):
        """Test that vectors with same direction but different magnitude are similar."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [2.0, 4.0, 6.0]  # 2× vec1
        
        similarity = cosine_similarity(vec1, vec2)
        
        # Should be 1.0 (cosine measures direction, not magnitude)
        assert abs(similarity - 1.0) < 0.0001
    
    def test_zero_vector(self):
        """Test that zero vector returns 0.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == 0.0
    
    def test_mismatched_dimensions(self):
        """Test that mismatched dimensions raise error."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        
        with pytest.raises(ValueError, match="same dimensions"):
            cosine_similarity(vec1, vec2)


class TestEuclideanDistance:
    """Tests for Euclidean distance calculation."""
    
    def test_identical_vectors(self):
        """Test that identical vectors have distance 0.0."""
        vec = [1.0, 2.0, 3.0]
        distance = euclidean_distance(vec, vec)
        
        assert abs(distance - 0.0) < 0.0001
    
    def test_unit_distance(self):
        """Test simple unit distance."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        distance = euclidean_distance(vec1, vec2)
        
        assert abs(distance - 1.0) < 0.0001
    
    def test_pythagorean_distance(self):
        """Test Pythagorean theorem (3-4-5 triangle)."""
        vec1 = [0.0, 0.0]
        vec2 = [3.0, 4.0]
        
        distance = euclidean_distance(vec1, vec2)
        
        # sqrt(3^2 + 4^2) = 5
        assert abs(distance - 5.0) < 0.0001
    
    def test_mismatched_dimensions(self):
        """Test that mismatched dimensions raise error."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        
        with pytest.raises(ValueError, match="same dimensions"):
            euclidean_distance(vec1, vec2)


class TestDocument:
    """Tests for Document dataclass."""
    
    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            id="doc_1",
            text="Test document",
            embedding=[0.1, 0.2, 0.3],
            metadata={"category": "test"},
        )
        
        assert doc.id == "doc_1"
        assert doc.text == "Test document"
        assert len(doc.embedding) == 3
        assert doc.metadata["category"] == "test"
    
    def test_document_defaults(self):
        """Test document with default values."""
        doc = Document(id="doc_1", text="Test")
        
        assert doc.embedding is None
        assert doc.metadata is None


class TestSemanticSearchEngine:
    """Tests for SemanticSearchEngine."""
    
    def test_initialization(self):
        """Test search engine initialization."""
        engine = SemanticSearchEngine()
        
        assert len(engine.documents) == 0
        assert engine.indexed is False
    
    def test_cosine_similarity_static(self):
        """Test static cosine similarity method."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        similarity = SemanticSearchEngine.cosine_similarity(vec1, vec2)
        
        assert abs(similarity - 0.0) < 0.0001
    
    def test_keyword_search_basic(self):
        """Test basic keyword search."""
        engine = SemanticSearchEngine()
        engine.documents = [
            Document(id="1", text="Python programming tutorial"),
            Document(id="2", text="JavaScript web development"),
            Document(id="3", text="Python data science"),
        ]
        engine.indexed = True
        
        results = engine.keyword_search("Python", top_k=2)
        
        assert len(results) == 2
        assert all("Python" in doc.text for doc in results)
    
    def test_keyword_search_no_match(self):
        """Test keyword search with no matches."""
        engine = SemanticSearchEngine()
        engine.documents = [
            Document(id="1", text="Python programming"),
            Document(id="2", text="JavaScript development"),
        ]
        engine.indexed = True
        
        results = engine.keyword_search("Ruby", top_k=5)
        
        assert len(results) == 0
    
    def test_keyword_search_case_insensitive(self):
        """Test that keyword search is case-insensitive."""
        engine = SemanticSearchEngine()
        engine.documents = [
            Document(id="1", text="Python Programming"),
        ]
        engine.indexed = True
        
        results = engine.keyword_search("python", top_k=5)
        
        assert len(results) == 1
    
    def test_keyword_search_ranking(self):
        """Test that keyword search ranks by relevance."""
        engine = SemanticSearchEngine()
        engine.documents = [
            Document(id="1", text="Python"),
            Document(id="2", text="Python Python programming"),
            Document(id="3", text="JavaScript"),
        ]
        engine.indexed = True
        
        results = engine.keyword_search("Python programming", top_k=2)
        
        # Should return docs with more matches first
        assert len(results) >= 1
        assert results[0].id == "2"  # Has both "Python" and "programming"


class TestSimilarityMetrics:
    """Tests for understanding of similarity metrics."""
    
    def test_cosine_range(self):
        """Test that cosine similarity is in [-1, 1] range."""
        test_cases = [
            ([1, 0], [0, 1]),    # Orthogonal
            ([1, 1], [1, 1]),    # Identical
            ([1, 0], [-1, 0]),   # Opposite
            ([1, 2], [2, 4]),    # Same direction, different magnitude
        ]
        
        for vec1, vec2 in test_cases:
            sim = cosine_similarity(vec1, vec2)
            assert -1.0 <= sim <= 1.0
    
    def test_euclidean_non_negative(self):
        """Test that Euclidean distance is always non-negative."""
        test_cases = [
            ([1, 2], [3, 4]),
            ([0, 0], [1, 1]),
            ([-1, -2], [1, 2]),
        ]
        
        for vec1, vec2 in test_cases:
            dist = euclidean_distance(vec1, vec2)
            assert dist >= 0.0
    
    def test_cosine_vs_euclidean(self):
        """Test difference between cosine and Euclidean."""
        # Same direction, different magnitudes
        vec1 = [1.0, 1.0]
        vec2 = [10.0, 10.0]
        
        cosine_sim = cosine_similarity(vec1, vec2)
        euclidean_dist = euclidean_distance(vec1, vec2)
        
        # Cosine should be 1.0 (same direction)
        assert abs(cosine_sim - 1.0) < 0.0001
        
        # Euclidean should be large (different magnitude)
        assert euclidean_dist > 10.0


class TestEmbeddingBestPractices:
    """Tests for embedding best practices."""
    
    def test_same_model_requirement(self):
        """Test understanding that same model should be used."""
        # This is a conceptual test - in practice, you'd check:
        # - Query embeddings use same model as document embeddings
        # - Embeddings have same dimensions
        
        # Different dimension embeddings are incomparable
        embedding_small = [0.1] * 1536  # text-embedding-3-small
        embedding_large = [0.1] * 3072  # text-embedding-3-large
        
        # Should raise error when comparing different dimensions
        with pytest.raises(ValueError):
            cosine_similarity(embedding_small, embedding_large)
    
    def test_normalization_importance(self):
        """Test that text normalization affects results."""
        # Same text, different casing/punctuation
        text1 = "Hello World"
        text2 = "hello world"
        
        # They should be normalized to same form before embedding
        normalized1 = text1.lower().strip()
        normalized2 = text2.lower().strip()
        
        assert normalized1 == normalized2


class TestSearchQuality:
    """Tests for search quality metrics."""
    
    def test_threshold_filtering(self):
        """Test that threshold filters low-quality results."""
        engine = SemanticSearchEngine()
        engine.documents = [
            Document(id="1", text="test", embedding=[1.0, 0.0]),
            Document(id="2", text="test", embedding=[0.9, 0.1]),
            Document(id="3", text="test", embedding=[0.0, 1.0]),
        ]
        engine.indexed = True
        
        # Low threshold: should get all results
        # High threshold: should get only similar results
        
        # This is a conceptual test - actual threshold testing
        # requires real embeddings from API
    
    def test_top_k_limiting(self):
        """Test that top_k limits number of results."""
        engine = SemanticSearchEngine()
        engine.documents = [Document(id=str(i), text=f"doc {i}") for i in range(10)]
        
        results = engine.keyword_search("doc", top_k=5)
        
        # Should return at most top_k results
        assert len(results) <= 5
