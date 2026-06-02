"""
Server-Sent Events (SSE) streaming for LLM responses.

SSE provides unidirectional server-to-client streaming over HTTP.
Perfect for progressive LLM token display in web applications.

Performance:
- Time to first token: 200-500ms (vs 3-10s blocking)
- Perceived latency: 5-20x faster
- Same total time, better UX
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator, Optional

from core.llm import stream as llm_stream
from core.telemetry import meters


logger = logging.getLogger(__name__)


async def stream_sse_response(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    **kwargs
) -> AsyncIterator[str]:
    """
    Stream LLM response as SSE events.
    
    Args:
        messages: Chat messages
        model: LLM model
        **kwargs: Additional parameters for LLM
        
    Yields:
        SSE-formatted strings: "data: {json}\\n\\n"
        
    Example:
        >>> async for event in stream_sse_response(messages):
        ...     print(event)  # "data: {\"content\": \"Hello\"}\\n\\n"
    
    Usage with FastAPI:
        from fastapi.responses import StreamingResponse
        
        @app.post("/chat/stream")
        async def chat_stream(request: ChatRequest):
            return StreamingResponse(
                stream_sse_response(request.messages),
                media_type="text/event-stream",
            )
    """
    start_time = time.perf_counter()
    first_token_time = None
    total_tokens = 0
    
    try:
        async for chunk in llm_stream(messages, model=model, **kwargs):
            # Track first token timing
            if first_token_time is None:
                first_token_time = time.perf_counter()
                ttft = (first_token_time - start_time) * 1000
                meters.record_latency_ms(ttft, "llm.streaming.first_token")
                logger.info(f"Time to first token: {ttft:.0f}ms")
            
            total_tokens += chunk.tokens
            
            # Format as SSE event
            data = {
                "content": chunk.content,
                "tokens": chunk.tokens,
                "finish_reason": chunk.finish_reason,
            }
            
            event = f"data: {json.dumps(data)}\n\n"
            yield event
        
        # Send completion event
        total_time = (time.perf_counter() - start_time) * 1000
        completion_data = {
            "done": True,
            "total_tokens": total_tokens,
            "total_time_ms": round(total_time, 2),
        }
        yield f"data: {json.dumps(completion_data)}\n\n"
        
        meters.record_latency_ms(total_time, "llm.streaming.total")
        logger.info(f"Streaming complete: {total_tokens} tokens in {total_time:.0f}ms")
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_data = {"error": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"


async def stream_with_heartbeat(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    heartbeat_interval: float = 15.0,
    **kwargs
) -> AsyncIterator[str]:
    """
    Stream with periodic heartbeat to keep connection alive.
    
    Args:
        messages: Chat messages
        model: LLM model
        heartbeat_interval: Seconds between heartbeats
        **kwargs: Additional parameters
        
    Yields:
        SSE events (content or heartbeat)
        
    Note:
        Some proxies close idle connections after 30-60s.
        Heartbeats prevent this during slow generation.
    """
    last_heartbeat = time.perf_counter()
    
    async def send_heartbeat():
        yield ": heartbeat\n\n"
    
    try:
        async for chunk in llm_stream(messages, model=model, **kwargs):
            # Reset heartbeat timer
            last_heartbeat = time.perf_counter()
            
            data = {
                "content": chunk.content,
                "tokens": chunk.tokens,
                "finish_reason": chunk.finish_reason,
            }
            yield f"data: {json.dumps(data)}\n\n"
            
            # Send heartbeat if needed
            if time.perf_counter() - last_heartbeat > heartbeat_interval:
                async for hb in send_heartbeat():
                    yield hb
                last_heartbeat = time.perf_counter()
        
        # Completion
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def buffered_stream(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    buffer_size: int = 5,
    min_interval_ms: float = 50,
    **kwargs
) -> AsyncIterator[str]:
    """
    Buffer chunks for smoother streaming.
    
    Args:
        messages: Chat messages
        model: LLM model
        buffer_size: Chunks to buffer before sending
        min_interval_ms: Minimum time between sends
        **kwargs: Additional parameters
        
    Yields:
        Buffered SSE events
        
    Use case:
        Reduce network overhead by sending chunks in batches.
        Trade slight latency for fewer HTTP frames.
    """
    buffer = []
    last_send_time = time.perf_counter()
    
    async for chunk in llm_stream(messages, model=model, **kwargs):
        buffer.append(chunk.content)
        
        # Send if buffer full or enough time passed
        time_since_send = (time.perf_counter() - last_send_time) * 1000
        should_send = (len(buffer) >= buffer_size) or (time_since_send >= min_interval_ms)
        
        if should_send and buffer:
            data = {
                "content": ''.join(buffer),
                "tokens": len(buffer),
            }
            yield f"data: {json.dumps(data)}\n\n"
            
            buffer = []
            last_send_time = time.perf_counter()
    
    # Flush remaining buffer
    if buffer:
        data = {"content": ''.join(buffer), "tokens": len(buffer)}
        yield f"data: {json.dumps(data)}\n\n"
    
    yield f"data: {json.dumps({'done': True})}\n\n"


async def stream_with_metadata(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    include_usage: bool = True,
    include_model: bool = True,
    **kwargs
) -> AsyncIterator[str]:
    """
    Stream with additional metadata in each event.
    
    Args:
        messages: Chat messages
        model: LLM model
        include_usage: Include token usage stats
        include_model: Include model name
        **kwargs: Additional parameters
        
    Yields:
        SSE events with metadata
    """
    total_tokens = 0
    
    async for chunk in llm_stream(messages, model=model, **kwargs):
        total_tokens += chunk.tokens
        
        data = {"content": chunk.content}
        
        if include_usage:
            data["usage"] = {
                "tokens_this_chunk": chunk.tokens,
                "total_tokens": total_tokens,
            }
        
        if include_model:
            data["model"] = model
        
        if chunk.finish_reason:
            data["finish_reason"] = chunk.finish_reason
        
        yield f"data: {json.dumps(data)}\n\n"
    
    # Final summary
    summary = {"done": True, "total_tokens": total_tokens}
    yield f"data: {json.dumps(summary)}\n\n"


# Client-side helper (for testing)
async def consume_sse_stream(url: str) -> AsyncIterator[dict]:
    """
    Consume SSE stream from a URL (client-side).
    
    Args:
        url: SSE endpoint URL
        
    Yields:
        Parsed JSON data from each event
        
    Example:
        >>> async for data in consume_sse_stream("http://localhost:8000/stream"):
        ...     if "content" in data:
        ...         print(data["content"], end="")
    """
    try:
        import aiohttp
    except ImportError:
        logger.error("aiohttp required for SSE client")
        return
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove "data: " prefix
                    try:
                        data = json.loads(json_str)
                        yield data
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse SSE data: {json_str}")


# Benchmarking helper
async def benchmark_streaming(
    messages: list[dict],
    model: str = "gpt-4o-mini",
) -> dict:
    """
    Benchmark streaming performance.
    
    Returns:
        Dict with timing metrics
    """
    start = time.perf_counter()
    first_token_time = None
    total_tokens = 0
    chunks_received = 0
    
    async for chunk in llm_stream(messages, model=model):
        if first_token_time is None:
            first_token_time = time.perf_counter()
        
        total_tokens += chunk.tokens
        chunks_received += 1
    
    total_time = time.perf_counter() - start
    ttft = (first_token_time - start) if first_token_time else 0
    
    return {
        "time_to_first_token_ms": round(ttft * 1000, 2),
        "total_time_ms": round(total_time * 1000, 2),
        "total_tokens": total_tokens,
        "chunks_received": chunks_received,
        "tokens_per_second": round(total_tokens / total_time, 2) if total_time > 0 else 0,
    }


# Example usage
if __name__ == "__main__":
    async def demo():
        messages = [
            {"role": "user", "content": "Write a short story about a robot."}
        ]
        
        print("SSE Streaming Demo\n" + "="*60)
        print("\nStreaming response:")
        print("-" * 60)
        
        async for event in stream_sse_response(messages):
            # Parse and display
            if event.startswith("data: "):
                data = json.loads(event[6:])
                if "content" in data:
                    print(data["content"], end="", flush=True)
                elif "done" in data:
                    print(f"\n\n{'='*60}")
                    print(f"Total tokens: {data.get('total_tokens', 'N/A')}")
                    print(f"Total time: {data.get('total_time_ms', 'N/A')}ms")
        
        # Benchmark
        print("\n\nBenchmark:")
        print("-" * 60)
        metrics = await benchmark_streaming(messages)
        for key, value in metrics.items():
            print(f"{key}: {value}")
    
    # Uncomment to run:
    # asyncio.run(demo())
    print("Demo available - uncomment asyncio.run(demo()) to test")
