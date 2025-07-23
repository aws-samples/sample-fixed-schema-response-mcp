"""
Tests for the request queue and rate limiting functionality.
"""

import asyncio
import pytest
import time
from unittest.mock import MagicMock, patch

from fixed_schema_mcp_server.core.request_queue import RequestQueue, RateLimiter, QueuedRequest, QueueFullError


class TestRateLimiter:
    """Tests for the RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring tokens within the rate limit."""
        # Create a rate limiter with 10 tokens per second
        rate_limiter = RateLimiter(10, 1.0, 10)
        
        # Acquire 5 tokens (should be immediate)
        wait_time = await rate_limiter.acquire(5)
        
        # Should not have to wait
        assert wait_time == 0.0
        
        # Internal state should be updated
        assert rate_limiter._tokens == 5
    
    @pytest.mark.asyncio
    async def test_acquire_exceeds_limit(self):
        """Test acquiring tokens that exceed the rate limit."""
        # Create a rate limiter with 10 tokens per second
        rate_limiter = RateLimiter(10, 1.0, 10)
        
        # Acquire all tokens
        wait_time = await rate_limiter.acquire(10)
        assert wait_time == 0.0
        assert rate_limiter._tokens == 0
        
        # Try to acquire more tokens
        wait_time = await rate_limiter.acquire(5)
        
        # Should have to wait
        assert wait_time > 0.0
        assert wait_time == pytest.approx(0.5, 0.1)  # Should wait about 0.5 seconds
    
    @pytest.mark.asyncio
    async def test_refill(self):
        """Test token refill over time."""
        # Create a rate limiter with 10 tokens per second
        rate_limiter = RateLimiter(10, 1.0, 10)
        
        # Acquire all tokens
        await rate_limiter.acquire(10)
        assert rate_limiter._tokens == 0
        
        # Wait for tokens to refill
        original_time = time.time
        try:
            # Mock time to advance by 0.5 seconds
            with patch('time.time', return_value=time.time() + 0.5):
                # Refill should add 5 tokens (10 tokens/sec * 0.5 sec)
                rate_limiter._refill()
                assert rate_limiter._tokens == pytest.approx(5, 0.1)
        finally:
            time.time = original_time
    
    @pytest.mark.asyncio
    async def test_burst_limit(self):
        """Test burst limit enforcement."""
        # Create a rate limiter with 10 tokens per second and burst limit of 15
        rate_limiter = RateLimiter(10, 1.0, 15)
        
        # Initial tokens should be at burst limit
        assert rate_limiter._tokens == 15
        
        # Acquire some tokens
        await rate_limiter.acquire(5)
        assert rate_limiter._tokens == 10
        
        # Wait for a long time (should refill to burst limit, not beyond)
        original_time = time.time
        try:
            # Mock time to advance by 10 seconds
            with patch('time.time', return_value=time.time() + 10):
                # Refill should add tokens up to burst limit
                rate_limiter._refill()
                assert rate_limiter._tokens == 15  # Capped at burst limit
        finally:
            time.time = original_time


class TestRequestQueue:
    """Tests for the RequestQueue class."""
    
    @pytest.mark.asyncio
    async def test_enqueue_and_process(self):
        """Test enqueueing and processing a request."""
        # Create a request queue
        queue = RequestQueue(rate_limit=100, rate_period=1.0)
        
        # Start the queue
        await queue.start()
        
        try:
            # Enqueue a request
            request_data = {"request_type": "test", "data": "test_data"}
            response = await queue.enqueue(request_data)
            
            # Check the response
            assert response["request_data"] == request_data
            assert "wait_time" in response
            assert "processed_at" in response
            assert "queued_at" in response
            assert "request_id" in response
        finally:
            # Stop the queue
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_queue_full(self):
        """Test queue full behavior."""
        # Create a request queue with small capacity
        queue = RequestQueue(rate_limit=100, rate_period=1.0, max_queue_size=2)
        
        # Start the queue but pause processing
        original_process = queue._process_queue
        queue._process_queue = MagicMock()  # Replace with mock to prevent processing
        await queue.start()
        
        try:
            # Enqueue requests up to capacity
            request1 = asyncio.create_task(queue.enqueue({"id": 1}))
            request2 = asyncio.create_task(queue.enqueue({"id": 2}))
            
            # Wait a bit to ensure they're queued
            await asyncio.sleep(0.1)
            
            # Try to enqueue one more (should fail)
            with pytest.raises(QueueFullError):
                await queue.enqueue({"id": 3})
            
            # Check metrics
            metrics = queue.get_metrics()
            assert metrics["current_queue_size"] == 2
            assert metrics["rejected_requests"] == 1
        finally:
            # Restore processing and stop the queue
            queue._process_queue = original_process
            await queue.stop()
            
            # Cancel pending tasks
            if not request1.done():
                request1.cancel()
            if not request2.done():
                request2.cancel()
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test that requests are processed in priority order."""
        # Create a request queue with rate limiting to control processing
        queue = RequestQueue(rate_limit=1, rate_period=1.0)
        
        # Start the queue
        await queue.start()
        
        try:
            # Enqueue requests with different priorities
            low_priority = asyncio.create_task(
                queue.enqueue({"id": "low"}, priority=RequestQueue.PRIORITY_LOW)
            )
            normal_priority = asyncio.create_task(
                queue.enqueue({"id": "normal"}, priority=RequestQueue.PRIORITY_NORMAL)
            )
            high_priority = asyncio.create_task(
                queue.enqueue({"id": "high"}, priority=RequestQueue.PRIORITY_HIGH)
            )
            
            # Wait for the high priority request to complete
            high_result = await high_priority
            assert high_result["request_data"]["id"] == "high"
            
            # Wait for the normal priority request to complete
            normal_result = await normal_priority
            assert normal_result["request_data"]["id"] == "normal"
            
            # Wait for the low priority request to complete
            low_result = await low_priority
            assert low_result["request_data"]["id"] == "low"
            
            # Check processing order through timestamps
            assert high_result["processed_at"] < normal_result["processed_at"]
            assert normal_result["processed_at"] < low_result["processed_at"]
        finally:
            # Stop the queue
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that requests are rate limited."""
        # Create a request queue with strict rate limiting
        queue = RequestQueue(rate_limit=2, rate_period=1.0, burst_limit=2)
        
        # Start the queue
        await queue.start()
        
        try:
            # Record start time
            start_time = time.time()
            
            # Enqueue multiple requests
            tasks = [
                asyncio.create_task(queue.enqueue({"id": i}))
                for i in range(5)
            ]
            
            # Wait for all requests to complete
            results = await asyncio.gather(*tasks)
            
            # Check that later requests had to wait
            end_time = time.time()
            elapsed = end_time - start_time
            
            # With rate limit of 2 per second, 5 requests should take at least 2 seconds
            assert elapsed >= 2.0
            
            # Check wait times in results
            wait_times = [result["wait_time"] for result in results]
            
            # First two requests should have minimal wait time
            assert wait_times[0] < 0.1
            assert wait_times[1] < 0.1
            
            # Later requests should have increasing wait times
            assert wait_times[2] > wait_times[0]
            assert wait_times[3] > wait_times[1]
            assert wait_times[4] > wait_times[2]
        finally:
            # Stop the queue
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_metrics(self):
        """Test queue metrics."""
        # Create a request queue
        queue = RequestQueue(rate_limit=10, rate_period=1.0, max_queue_size=10)
        
        # Start the queue
        await queue.start()
        
        try:
            # Enqueue some requests
            for i in range(3):
                await queue.enqueue({"id": i})
            
            # Check metrics
            metrics = queue.get_metrics()
            assert metrics["total_requests"] == 3
            assert metrics["processed_requests"] == 3
            assert metrics["rejected_requests"] == 0
            assert metrics["current_queue_size"] == 0
            assert metrics["queue_capacity"] == 10
            assert "avg_wait_time" in metrics
        finally:
            # Stop the queue
            await queue.stop()