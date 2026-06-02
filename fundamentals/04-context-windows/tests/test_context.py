"""
Tests for context window management functionality.
"""

import pytest
from fundamentals.fundamentals_04_context_windows.sliding_window import (
    count_tokens,
    split_into_windows,
    combine_results,
)
from fundamentals.fundamentals_04_context_windows.context_pruning import (
    keyword_filter,
    extractive_summarization,
    split_into_sentences,
    prune_to_budget,
)


class TestTokenCounting:
    """Tests for token counting."""
    
    def test_count_tokens_basic(self):
        """Test basic token counting."""
        text = "Hello, world!"
        count = count_tokens(text)
        
        assert count > 0
        assert 3 <= count <= 6  # Typically 4-5 tokens
    
    def test_count_tokens_empty(self):
        """Test counting empty string."""
        count = count_tokens("")
        assert count == 0
    
    def test_count_tokens_long(self):
        """Test counting longer text."""
        text = "The quick brown fox " * 100
        count = count_tokens(text)
        
        assert count > 100
        assert count < 1000


class TestSlidingWindow:
    """Tests for sliding window functionality."""
    
    def test_split_single_window(self):
        """Test splitting text that fits in one window."""
        text = "Short text"
        windows = split_into_windows(text, window_size=100, overlap=10)
        
        assert len(windows) == 1
        assert windows[0].text == text
        assert windows[0].chunk_id == 0
    
    def test_split_multiple_windows(self):
        """Test splitting text into multiple windows."""
        text = "word " * 1000  # ~1000 tokens
        windows = split_into_windows(text, window_size=200, overlap=50)
        
        # Should create multiple windows
        assert len(windows) > 1
        
        # Check window properties
        for i, window in enumerate(windows):
            assert window.chunk_id == i
            assert window.token_count > 0
            assert window.start_pos < window.end_pos
    
    def test_window_overlap(self):
        """Test that windows have proper overlap."""
        text = "word " * 500
        overlap = 50
        window_size = 200
        
        windows = split_into_windows(text, window_size=window_size, overlap=overlap)
        
        if len(windows) > 1:
            # Check that second window starts before first ends
            assert windows[1].start_pos < windows[0].end_pos
            # Overlap should be approximately as specified
            actual_overlap = windows[0].end_pos - windows[1].start_pos
            assert 0 < actual_overlap <= overlap * 1.5  # Allow some variance
    
    def test_window_token_counts(self):
        """Test that window token counts are within limits."""
        text = "word " * 1000
        window_size = 200
        
        windows = split_into_windows(text, window_size=window_size)
        
        for window in windows:
            # Each window should be <= window_size (except maybe last)
            assert window.token_count <= window_size + 10  # Small buffer


class TestCombineResults:
    """Tests for combining window results."""
    
    def test_combine_concatenate(self):
        """Test concatenation strategy."""
        results = [
            {"result": "First window result"},
            {"result": "Second window result"},
        ]
        
        combined = combine_results(results, strategy="concatenate")
        
        assert "First window result" in combined
        assert "Second window result" in combined
    
    def test_combine_deduplicate(self):
        """Test deduplication strategy."""
        results = [
            {"result": "Same sentence. Different sentence."},
            {"result": "Same sentence. Another sentence."},
        ]
        
        combined = combine_results(results, strategy="deduplicate")
        
        # Should not duplicate "Same sentence"
        assert combined.count("Same sentence") == 1
    
    def test_combine_empty(self):
        """Test combining empty results."""
        results = [{"result": ""}]
        combined = combine_results(results)
        
        # Should handle empty gracefully
        assert combined == ""


class TestKeywordFiltering:
    """Tests for keyword filtering."""
    
    def test_keyword_filter_basic(self):
        """Test basic keyword filtering."""
        text = "Revenue increased. Weather was nice. Profits grew."
        keywords = ["revenue", "profit"]
        
        filtered = keyword_filter(text, keywords)
        
        assert "Revenue" in filtered
        assert "Profits" in filtered
        assert "Weather" not in filtered
    
    def test_keyword_filter_case_insensitive(self):
        """Test that keyword filtering is case-insensitive."""
        text = "REVENUE increased. weather was nice."
        keywords = ["revenue"]
        
        filtered = keyword_filter(text, keywords)
        
        assert "REVENUE" in filtered
        assert "weather" not in filtered
    
    def test_keyword_filter_no_match(self):
        """Test filtering with no matching keywords."""
        text = "The weather was nice today."
        keywords = ["revenue", "profit"]
        
        filtered = keyword_filter(text, keywords)
        
        assert filtered == ""
    
    def test_keyword_filter_multiple_keywords(self):
        """Test filtering with multiple keywords."""
        text = "Revenue grew. Costs decreased. Weather changed. Profit increased."
        keywords = ["revenue", "cost", "profit"]
        
        filtered = keyword_filter(text, keywords)
        
        assert "Revenue" in filtered
        assert "Costs" in filtered
        assert "Profit" in filtered
        assert "Weather" not in filtered


class TestSentenceSplitting:
    """Tests for sentence splitting."""
    
    def test_split_sentences_basic(self):
        """Test basic sentence splitting."""
        text = "First sentence. Second sentence. Third sentence."
        sentences = split_into_sentences(text)
        
        assert len(sentences) == 3
        assert "First sentence" in sentences
        assert "Third sentence" in sentences
    
    def test_split_sentences_multiple_punctuation(self):
        """Test splitting with different punctuation."""
        text = "First sentence. Question? Exclamation! End."
        sentences = split_into_sentences(text)
        
        assert len(sentences) >= 3
    
    def test_split_sentences_empty(self):
        """Test splitting empty text."""
        sentences = split_into_sentences("")
        assert sentences == []


class TestExtractiveSummarization:
    """Tests for extractive summarization."""
    
    def test_extractive_basic(self):
        """Test basic extractive summarization."""
        text = """
        Artificial intelligence is important. AI transforms industries.
        The weather is nice. Machine learning is a subset of AI.
        Coffee tastes good. Deep learning uses neural networks.
        """
        
        summary = extractive_summarization(text, num_sentences=3)
        
        # Should extract AI-related sentences (most frequent terms)
        assert len(split_into_sentences(summary)) <= 3
    
    def test_extractive_short_text(self):
        """Test extractive summarization on short text."""
        text = "One sentence."
        summary = extractive_summarization(text, num_sentences=5)
        
        # Should return original if shorter than target
        assert summary.strip() == text.strip()
    
    def test_extractive_token_reduction(self):
        """Test that summarization reduces token count."""
        text = ("This is a sentence. " * 100)
        
        original_tokens = count_tokens(text)
        summary = extractive_summarization(text, num_sentences=10)
        summary_tokens = count_tokens(summary)
        
        # Summary should be shorter
        assert summary_tokens < original_tokens


class TestPruneToBudget:
    """Tests for pruning to budget."""
    
    def test_prune_within_budget(self):
        """Test pruning text already within budget."""
        text = "Short text"
        pruned = prune_to_budget(text, max_tokens=100, method="truncate")
        
        # Should return original if within budget
        assert text in pruned
    
    def test_prune_truncate(self):
        """Test truncation method."""
        text = "word " * 1000
        max_tokens = 100
        
        pruned = prune_to_budget(text, max_tokens, method="truncate")
        
        # Should be within budget
        assert count_tokens(pruned) <= max_tokens + 10
        assert "[truncated]" in pruned
    
    def test_prune_extractive(self):
        """Test extractive method."""
        text = ("Sentence number one. " * 50)
        max_tokens = 100
        
        pruned = prune_to_budget(text, max_tokens, method="extractive")
        
        # Should be within budget
        assert count_tokens(pruned) <= max_tokens * 1.2  # Allow buffer
    
    def test_prune_preserves_content(self):
        """Test that pruning preserves some content."""
        text = "Important information here. More important data."
        max_tokens = 50
        
        pruned = prune_to_budget(text, max_tokens, method="truncate")
        
        # Should preserve start of text
        assert "Important" in pruned


class TestCostOptimization:
    """Tests for cost optimization through context management."""
    
    def test_pruning_reduces_cost(self):
        """Test that pruning reduces token count and thus cost."""
        long_text = "word " * 10000
        short_text = prune_to_budget(long_text, max_tokens=1000, method="truncate")
        
        long_tokens = count_tokens(long_text)
        short_tokens = count_tokens(short_text)
        
        # Should significantly reduce tokens
        assert short_tokens < long_tokens * 0.2
    
    def test_window_count_affects_cost(self):
        """Test that number of windows affects total cost."""
        text = "word " * 5000
        
        # Large windows (fewer windows)
        windows_large = split_into_windows(text, window_size=2000, overlap=100)
        
        # Small windows (more windows)
        windows_small = split_into_windows(text, window_size=500, overlap=100)
        
        # More windows = more API calls = higher cost
        assert len(windows_small) > len(windows_large)
