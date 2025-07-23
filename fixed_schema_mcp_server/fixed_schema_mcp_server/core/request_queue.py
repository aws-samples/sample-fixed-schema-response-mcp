"""
Request queue functionality for the Fixed Schema Response MCP Server.

This module provides functionality for queuing and processing requests,
including rate limiting and prioritization.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union, Callable, Awaitable

logger = logging.getLogger(__name__)

class QueueFullError(Exception):
    """Exception raised when the queue is full."""
    pass

class RequestQueue:
    """
    Request queue for the Fixed Schema Response MCP Server.
    
    This class is responsible for queuing and processing requests,
    including rate limiting and prioritization.
    """
    
    def __init__(
        self,
        rate_limit: float = 10.0,
        rate_period: float = 60.0,
        burst_limit: Optional[int] = None,
        max_queue_size: int = 100
    ):
        """
        Initialize the request queue.
        
        Args:
            rate_limit: The rate limit for requests (requests per rate_period)
            rate_period: The time period for the rate limit (in seconds)
            burst_limit: The maximum number of requests that can be processed in a burst
            max_queue_size: The maximum size of the queue
        """
        self._rate_limit = rate_limit
        self._rate_period = rate_period
        self._burst_limit = burst_limit
        self._max_queue_size = max_queue_size
        
        self._queue = asyncio.PriorityQueue()
        self._running = False
        self._task = None
        self._last_request_time = 0
        self._request_count = 0
        self._request_times = []
        
        # Metrics
        self._processed_count = 0
        self._rejected_count = 0
        self._queue_wait_times = []
        self._max_queue_wait_time = 0
        self._min_queue_wait_time = float('inf')
        self._total_queue_wait_time = 0
    
    async def start(self) -> None:
        """Start the request queue processor."""
        if self._running:
            logger.warning("Request queue is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info("Request queue started")
    
    async def stop(self) -> None:
        """Stop the request queue processor."""
        if not self._running:
            logger.warning("Request queue is not running")
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("Request queue stopped")
    
    async def enqueue(
        self,
        request_data: Dict[str, Any],
        priority: int = 50,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enqueue a request for processing.
        
        Args:
            request_data: The request data
            priority: The priority of the request (lower values have higher priority)
            request_id: Optional request ID for tracking
            
        Returns:
            A dictionary containing the dequeued request data and metadata
            
        Raises:
            QueueFullError: If the queue is full
        """
        # Check if the queue is full
        if self._queue.qsize() >= self._max_queue_size:
            logger.warning(f"Request queue is full ({self._queue.qsize()} items)")
            raise QueueFullError(f"Request queue is full ({self._queue.qsize()} items)")
        
        # Check if we're rate limited
        if not self._check_rate_limit():
            logger.warning("Rate limit exceeded")
            raise QueueFullError("Rate limit exceeded")
        
        # Create a future to wait for the result
        result_future = asyncio.Future()
        
        # Enqueue the request
        enqueue_time = time.time()
        queue_item = (priority, enqueue_time, request_data, result_future, request_id)
        await self._queue.put(queue_item)
        
        # Wait for the result
        result = await result_future
        
        # Calculate wait time
        dequeue_time = time.time()
        wait_time = dequeue_time - enqueue_time
        
        # Update metrics
        self._update_wait_time_metrics(wait_time)
        
        # Return the result with metadata
        return {
            "request_data": result,
            "wait_time": wait_time,
            "queue_position": self._queue.qsize()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get queue metrics.
        
        Returns:
            A dictionary containing queue metrics
        """
        return {
            "queue_size": self._queue.qsize(),
            "processed_count": self._processed_count,
            "rejected_count": self._rejected_count,
            "avg_wait_time": self._total_queue_wait_time / max(1, len(self._queue_wait_times)),
            "max_wait_time": self._max_queue_wait_time,
            "min_wait_time": self._min_queue_wait_time if self._min_queue_wait_time != float('inf') else 0,
            "rate_limit": self._rate_limit,
            "rate_period": self._rate_period,
            "burst_limit": self._burst_limit,
            "max_queue_size": self._max_queue_size
        }
    
    async def _process_queue(self) -> None:
        """
        Process items from the queue.
        
        This method runs in a loop, dequeuing items and processing them.
        """
        while self._running:
            try:
                # Get the next item from the queue
                priority, enqueue_time, request_data, result_future, request_id = await self._queue.get()
                
                # Process the request
                try:
                    # Update the request count and times
                    self._request_count += 1
                    self._request_times.append(time.time())
                    self._last_request_time = time.time()
                    
                    # Set the result
                    result_future.set_result(request_data)
                    
                    # Update metrics
                    self._processed_count += 1
                    
                except Exception as e:
                    # Set the exception
                    result_future.set_exception(e)
                    
                    # Update metrics
                    self._rejected_count += 1
                
                # Mark the item as done
                self._queue.task_done()
                
            except asyncio.CancelledError:
                # Task was cancelled, exit the loop
                logger.info("Queue processing task cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing queue item: {e}")
    
    def _check_rate_limit(self) -> bool:
        """
        Check if the rate limit has been exceeded.
        
        Returns:
            True if the request can be processed, False if the rate limit has been exceeded
        """
        # Remove old request times
        current_time = time.time()
        cutoff_time = current_time - self._rate_period
        self._request_times = [t for t in self._request_times if t > cutoff_time]
        
        # Check if we've exceeded the rate limit
        if len(self._request_times) >= self._rate_limit:
            return False
        
        # Check if we've exceeded the burst limit
        if self._burst_limit is not None and len(self._request_times) >= self._burst_limit:
            return False
        
        return True
    
    def _update_wait_time_metrics(self, wait_time: float) -> None:
        """
        Update wait time metrics.
        
        Args:
            wait_time: The wait time to record
        """
        self._queue_wait_times.append(wait_time)
        self._total_queue_wait_time += wait_time
        
        if wait_time > self._max_queue_wait_time:
            self._max_queue_wait_time = wait_time
        
        if wait_time < self._min_queue_wait_time:
            self._min_queue_wait_time = wait_time
        
        # Limit the number of wait times we store
        if len(self._queue_wait_times) > 1000:
            removed_time = self._queue_wait_times.pop(0)
            self._total_queue_wait_time -= removed_time