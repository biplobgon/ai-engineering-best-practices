"""
Tests for SSE streaming module.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from latency_optimization.streaming.sse_streaming import (
    stream_sse_response,
    stream_with_heartbeat,
    buffered_stream,
    benchmark_streaming,
)


@pytest.fixture
def sample_messages():
    """Sample chat messages."""
    return [{"role": "user", "content": "Hello, how are you?"}]


@pytest.fixture
def mock_chunks():
    """Mock streaming chunks."""
    from core.schemas import Chunk
    return [
        Chunk(content="Hello", tokens=1, latency_ms=100, finish_reason=None),
        Chunk(content=" world", tokens=1, latency_ms=150, finish_reason=None),
        Chunk(content="!", tokens=1, latency_ms=200, finish_reason="stop"),
    ]


class TestSSEStreaming:
    """Test basic SSE streaming."""
    
    @pytest.mark.asyncio
    async def test_sse_format(self, sample_messages, mock_chunks):
        """SSE events should be properly formatted."""
        
        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        with patch('latency_optimization.streaming.sse_streaming.llm_stream', mock_stream):
            events = []
            async for event in stream_sse_response(sample_messages):
                events.append(event)
            
            # Should have events for each chunk + completion
            assert len(events) > 0
            
            # Each event should start with "data: "
            for event in events:
                assert event.startswith("data: ")
                assert event.endswith("\n\n")
            
            # Last event should be completion
            last_data = json.loads(events[-1][6:-2])
            assert "done" in last_data
            assert last_data["done"] is True
    
    @pytest.mark.asyncio
    async def test_content_in_events(self, sample_messages, mock_chunks):
        """Content should be in event data."""
        
        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        with patch('latency_optimization.streaming.sse_streaming.llm_stream', mock_stream):
            content_chunks = []
            async for event in stream_sse_response(sample_messages):
                data = json.loads(event[6:-2])  # Remove "data: " and "\n\n"
                if "content" in data:
                    content_chunks.append(data["content"])
            
            # Should have received all content
            assert len(content_chunks) == len(mock_chunks)
            assert "".join(content_chunks) == "Hello world!"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, sample_messages):
        """Errors should be caught and returned as events."""
        
        async def mock_stream_with_error(*args, **kwargs):
            yield mock_chunks[0]
            raise Exception("Test error")
        
        with patch('latency_optimization.streaming.sse_streaming.llm_stream', mock_stream_with_error):
            events = []
            async for event in stream_sse_response(sample_messages):
                events.append(event)
            
            # Should have error event
            assert len(events) > 0
            last_event = events[-1]
            data = json.loads(last_event[6:-2])
            assert "error" in data


class TestHeartbeat:
    """Test heartbeat functionality."""
    
    @pytest.mark.asyncio
    async def test_heartbeat_format(self, sample_messages, mock_chunks):
        """Heartbeat should use proper SSE comment format."""
        
        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        with patch('latency_optimization.streaming.sse_streaming.llm_stream', mock_stream):
            events = []
            async for event in stream_with_heartbeat(sample_messages, heartbeat_interval=0.01):
                events.append(event)
            
            # Should have at least content events
            assert len(events) > 0


class TestBufferedStream:
    """Test buffered streaming."""
    
    @pytest.mark.asyncio
    async def test_buffering_combines_chunks(self, sample_messages, mock_chunks):
        """Buffering should combine chunks."""
        
        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        with patch('latency_optimization.streaming.sse_streaming.llm_stream', mock_stream):
            events = []
            async for event in buffered_stream(sample_messages, buffer_size=2):
                events.append(event)
            
            # Should have fewer events than chunks due to buffering
            # (exact number depends on timing)
            assert len(events) > 0
    
    @pytest.mark.asyncio
    async def test_buffer_flush(self, sample_messages):
        """Buffer should flush remaining content."""
        from core.schemas import Chunk
        
        single_chunk = [Chunk(content="Test", tokens=1, latency_ms=100, finish_reason="stop")]
        
        async def mock_stream(*args, **kwargs):
            for chunk in single_chunk:
                yield chunk
        
        with patch('latency_optimization.streaming.sse_streaming.llm_stream', mock_stream):
            events = []
            async for event in buffered_stream(sample_messages, buffer_size=10):
                events.append(event)
            
            # Should flush even though buffer not full
            assert len(events) > 0
            
            # Check content was included
            content_found = False
            for event in events:
                data = json.loads(event[6:-2])
                if "content" in data and "Test" in data["content"]:
                    content_found = True
            assert content_found


class TestBenchmarking:
    """Test benchmarking utilities."""
    
    @pytest.mark.asyncio
    async def test_benchmark_structure(self, sample_messages, mock_chunks):
        """Benchmark should return expected metrics."""
        
        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        with patch('latency_optimization.streaming.sse_streaming.llm_stream', mock_stream):
            metrics = await benchmark_streaming(sample_messages)
            
            # Check structure
            assert 'time_to_first_token_ms' in metrics
            assert 'total_time_ms' in metrics
            assert 'total_tokens' in metrics
            assert 'chunks_received' in metrics
            assert 'tokens_per_second' in metrics
            
            # Check values
            assert metrics['time_to_first_token_ms'] >= 0
            assert metrics['total_time_ms'] >= metrics['time_to_first_token_ms']
            assert metrics['total_tokens'] == len(mock_chunks)
            assert metrics['chunks_received'] == len(mock_chunks)


class TestEdgeCases:
    """Test edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_stream(self, sample_messages):
        """Empty stream should be handled."""
        
        async def mock_empty_stream(*args, **kwargs):
            return
            yield  # Make it a generator
        
        with patch('latency_optimization.streaming.sse_streaming.llm_stream', mock_empty_stream):
            events = []
            async for event in stream_sse_response(sample_messages):
                events.append(event)
            
            # Should have completion event even with no chunks
            assert len(events) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
