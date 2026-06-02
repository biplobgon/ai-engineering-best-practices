"""
Tests for summarization pipelines.
"""

import pytest
from unittest.mock import AsyncMock, patch
from token_optimization.compression.summarization_pipelines import (
    summarize_once,
    recursive_summarize,
    chunk_and_summarize,
    adaptive_summarize,
    summarize_with_metrics,
)


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Artificial intelligence has made remarkable progress in recent years.
    Large language models can understand and generate human-like text.
    However, these models come with significant costs and latency challenges.
    Token optimization is critical for production deployments.
    Various techniques can reduce token usage by 60-90%.
    """ * 20  # Make it long enough to require summarization


class TestSummarizeOnce:
    """Test single-pass summarization."""
    
    @pytest.mark.asyncio
    async def test_already_within_target(self):
        """Short text should be returned as-is."""
        text = "Short text here."
        result = await summarize_once(text, target_tokens=100)
        assert result == text
    
    @pytest.mark.asyncio
    async def test_summarization_reduces_tokens(self, sample_text):
        """Summarization should reduce token count."""
        with patch('token_optimization.compression.summarization_pipelines.chat') as mock_chat:
            # Mock LLM response
            mock_chat.return_value = AsyncMock(text="Summarized version of the text.")
            
            result = await summarize_once(sample_text, target_tokens=50)
            
            # Should have called chat
            assert mock_chat.called
            # Should return mocked summary
            assert "Summarized" in result


class TestRecursiveSummarize:
    """Test recursive summarization."""
    
    @pytest.mark.asyncio
    async def test_recursive_with_mock(self, sample_text):
        """Recursive summarization should reduce in multiple passes."""
        call_count = 0
        
        async def mock_summarize(text, target_tokens, **kwargs):
            nonlocal call_count
            call_count += 1
            # Each pass reduces by 50%
            return text[:len(text)//2]
        
        with patch('token_optimization.compression.summarization_pipelines.summarize_once', mock_summarize):
            result = await recursive_summarize(sample_text, target_tokens=10, max_passes=3)
            
            # Should have made multiple passes
            assert call_count > 0
            # Result should be shorter
            assert len(result) < len(sample_text)
    
    @pytest.mark.asyncio
    async def test_early_exit_when_target_reached(self):
        """Should stop early if target is reached."""
        text = "Short text."
        result = await recursive_summarize(text, target_tokens=100, max_passes=5)
        
        # Should return immediately
        assert result == text


class TestChunkAndSummarize:
    """Test chunk-based summarization."""
    
    @pytest.mark.asyncio
    async def test_chunking_long_text(self, sample_text):
        """Long text should be chunked and summarized."""
        with patch('token_optimization.compression.summarization_pipelines.summarize_once') as mock_summarize:
            mock_summarize.return_value = "Summary"
            
            result = await chunk_and_summarize(sample_text, chunk_size=100, target_tokens=50)
            
            # Should have called summarize_once multiple times (once per chunk + final)
            assert mock_summarize.call_count > 1


class TestAdaptiveSummarize:
    """Test adaptive strategy selection."""
    
    @pytest.mark.asyncio
    async def test_adaptive_selects_appropriate_method(self):
        """Adaptive should choose method based on text length."""
        
        # Short text: single pass
        short_text = "Short text." * 10
        with patch('token_optimization.compression.summarization_pipelines.summarize_once') as mock_once:
            mock_once.return_value = short_text
            result = await adaptive_summarize(short_text, target_tokens=100)
            # Should use single pass for text close to target
            assert mock_once.called or result == short_text
        
        # Long text: should use more aggressive method
        long_text = "Long text. " * 1000
        with patch('token_optimization.compression.summarization_pipelines.chunk_and_summarize') as mock_chunk:
            mock_chunk.return_value = "Summary"
            result = await adaptive_summarize(long_text, target_tokens=10)
            # For very long text, should use chunking
            assert mock_chunk.called or len(result) < len(long_text)


class TestMetrics:
    """Test metrics tracking."""
    
    @pytest.mark.asyncio
    async def test_metrics_structure(self, sample_text):
        """Metrics should contain expected fields."""
        with patch('token_optimization.compression.summarization_pipelines.summarize_once') as mock_summarize:
            mock_summarize.return_value = "Short summary."
            
            result = await summarize_with_metrics(sample_text, target_tokens=50, method="once")
            
            # Check structure
            assert 'text' in result
            assert 'tokens_before' in result
            assert 'tokens_after' in result
            assert 'reduction_pct' in result
            assert 'latency_ms' in result
            assert 'method' in result
            
            # Check values
            assert result['tokens_before'] > 0
            assert result['tokens_after'] > 0
            assert 0 <= result['reduction_pct'] <= 100
            assert result['latency_ms'] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_empty_text(self):
        """Empty text should be handled gracefully."""
        result = await summarize_once("", target_tokens=100)
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_very_large_text(self):
        """Very large text should not crash."""
        huge_text = "word " * 100000
        
        with patch('token_optimization.compression.summarization_pipelines.chat') as mock_chat:
            mock_chat.return_value = AsyncMock(text="Summary")
            
            result = await summarize_once(huge_text, target_tokens=100)
            assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
