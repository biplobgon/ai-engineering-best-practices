"""
Tests for token pruning module.
"""

import pytest
from token_optimization.compression.token_pruning import (
    prune_tokens,
    prune_filler_words,
    remove_noise_patterns,
    prune_with_metrics,
    batch_prune,
    count_tokens,
)


class TestFillerWordRemoval:
    """Test filler word removal."""
    
    def test_basic_fillers(self):
        text = "Um, well, I think we should focus on this."
        result = prune_filler_words(text)
        assert "um" not in result.lower()
        assert "well" not in result.lower()
        assert "focus" in result.lower()
    
    def test_multi_word_fillers(self):
        text = "You know, at the end of the day, we need results."
        result = prune_filler_words(text)
        assert "you know" not in result.lower()
        assert "end of the day" not in result.lower()
        assert "results" in result.lower()
    
    def test_preserves_meaning(self):
        text = "The product is good."
        result = prune_filler_words(text)
        assert result.lower().strip() == "the product is good."
    
    def test_empty_string(self):
        assert prune_filler_words("") == ""
    
    def test_only_fillers(self):
        text = "Um, uh, well, you know"
        result = prune_filler_words(text)
        assert len(result.strip()) < len(text) // 2


class TestNoisePatternRemoval:
    """Test noise pattern removal."""
    
    def test_multiple_spaces(self):
        text = "This  has    multiple   spaces"
        result = remove_noise_patterns(text)
        assert "  " not in result
    
    def test_multiple_newlines(self):
        text = "Line 1\n\n\n\nLine 2"
        result = remove_noise_patterns(text)
        assert "\n\n\n" not in result
    
    def test_repeated_punctuation(self):
        text = "Really!!!! Amazing???"
        result = remove_noise_patterns(text)
        assert "!!!" not in result
        assert "???" not in result
        assert "!" in result
        assert "?" in result
    
    def test_preserves_single_newline(self):
        text = "Line 1\n\nLine 2"
        result = remove_noise_patterns(text)
        assert "\n\n" in result  # Double newline preserved


class TestFullPruning:
    """Test complete pruning pipeline."""
    
    def test_combined_pruning(self):
        text = "Um,  well,   I  think  we should    focus."
        result = prune_tokens(text)
        assert len(result) < len(text)
        assert "focus" in result.lower()
    
    def test_preserve_code_blocks(self):
        text = """
        Some text here.
        ```python
        def function():  # Multiple spaces
            pass
        ```
        More text.
        """
        result = prune_tokens(text, preserve_code=True)
        assert "def function():" in result
        assert "  # Multiple spaces" in result  # Preserved in code block
    
    def test_no_code_preservation(self):
        text = "```python\ndef   foo():  pass\n```"
        result = prune_tokens(text, preserve_code=False, remove_noise=True)
        # Should normalize spaces
        assert "   " not in result
    
    def test_selective_pruning(self):
        text = "Um,  well,  focus here."
        
        # Only fillers
        result1 = prune_tokens(text, remove_fillers=True, remove_noise=False)
        assert "  " in result1  # Spaces preserved
        assert "um" not in result1.lower()
        
        # Only noise
        result2 = prune_tokens(text, remove_fillers=False, remove_noise=True)
        assert "  " not in result2
        assert "um" in result2.lower()


class TestMetrics:
    """Test metrics and batch processing."""
    
    def test_metrics_tracking(self):
        text = "Um, well, I think we should focus on this. " * 10
        result = prune_with_metrics(text)
        
        assert 'text' in result
        assert 'tokens_before' in result
        assert 'tokens_after' in result
        assert 'reduction_pct' in result
        assert result['tokens_after'] < result['tokens_before']
        assert 0 <= result['reduction_pct'] <= 100
    
    def test_no_compression_needed(self):
        text = "Clean text here"
        result = prune_with_metrics(text)
        # Should have minimal reduction
        assert result['reduction_pct'] < 10
    
    def test_batch_processing(self):
        texts = [
            "Um, first text",
            "Well, second text",
            "You know, third text",
        ]
        results = batch_prune(texts)
        
        assert len(results) == len(texts)
        for original, compressed in zip(texts, results):
            assert len(compressed) <= len(original)


class TestTokenCounting:
    """Test token counting."""
    
    def test_basic_counting(self):
        text = "Hello world"
        count = count_tokens(text)
        assert count > 0
        assert count < len(text)  # Tokens < chars
    
    def test_empty_string(self):
        assert count_tokens("") == 0
    
    def test_consistency(self):
        text = "This is a test sentence."
        count1 = count_tokens(text)
        count2 = count_tokens(text)
        assert count1 == count2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_input(self):
        assert prune_tokens("") == ""
    
    def test_unicode_handling(self):
        text = "Hello 世界 🌍"
        result = prune_tokens(text)
        assert "世界" in result
        assert "🌍" in result
    
    def test_very_long_text(self):
        text = "word " * 10000
        result = prune_tokens(text)
        # Should complete without error
        assert isinstance(result, str)
    
    def test_special_characters(self):
        text = "Test @#$% special &*() characters"
        result = prune_tokens(text)
        assert len(result) > 0


# Benchmarks
class TestPerformance:
    """Performance benchmarks."""
    
    def test_pruning_speed(self, benchmark):
        text = "Um, well, I think we should focus on the customer experience. " * 100
        
        result = benchmark(prune_tokens, text)
        assert len(result) < len(text)
    
    def test_batch_speed(self, benchmark):
        texts = ["Um, sample text " * 10] * 50
        
        results = benchmark(batch_prune, texts)
        assert len(results) == len(texts)


# Integration test
def test_realistic_scenario():
    """Test with realistic chat transcript."""
    chat_transcript = """
    User: Um, so, like, I was wondering if you could, you know, help me with this problem?
    
    Agent: Well, actually, I think I can definitely help you with that. What seems to be the issue?
    
    User: So, basically, at the end of the day, I need to, kind of, optimize my prompts.
    
    Agent: I see. Well, honestly, the first step is to, you know, remove unnecessary words.
    """
    
    result = prune_with_metrics(chat_transcript)
    
    # Should have significant reduction
    assert result['reduction_pct'] > 20
    
    # Should preserve key information
    assert "help" in result['text'].lower()
    assert "optimize" in result['text'].lower()
    assert "prompts" in result['text'].lower()
    
    # Should remove fillers
    assert result['text'].count("um") == 0
    assert result['text'].count("you know") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
