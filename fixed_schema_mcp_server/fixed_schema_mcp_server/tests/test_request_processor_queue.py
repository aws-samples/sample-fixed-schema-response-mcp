"""
Tests for the request processor with queuing functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fixed_schema_mcp_server.core.request_processor import RequestProcessor
from fixed_schema_mcp_server.core.exceptions import RequestValidationError, RequestProcessingError
from fixed_schema_mcp_server.core.request_queue import QueueFullError


class TestRequestProcessorQueue:
    """Test cases for the RequestProcessor class with queuing enabled."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.mock_model_manager = MagicMock()
        self.mock_model_manager.generate_response = AsyncMock()
        
        self.mock_schema_manager = MagicMock()
        self.mock_schema_manager.get_schema = MagicMock()
        self.mock_schema_manager.validate_against_schema = MagicMock()
        self.mock_schema_manager.get_all_schema_names = MagicMock()
        
        self.mock_response_processor = MagicMock()
        self.mock_response_processor.process_response = AsyncMock()
        self.mock_response_processor.validate_response = MagicMock()
        self.mock_response_processor.fix_response = MagicMock()
        
        # Create the request processor with mock dependencies and queuing enabled
        self.request_processor = RequestProcessor(
            model_manager=self.mock_model_manager,
            schema_manager=self.mock_schema_manager,
            response_processor=self.mock_response_processor,
            rate_limit=10.0,
            rate_period=1.0,
            max_queue_size=5,
            enable_queue=True
        )
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping the request processor."""
        # Start the request processor
        await self.request_processor.start()
        
        # Stop the request processor
        await self.request_processor.stop()
    
    @pytest.mark.asyncio
    async def test_process_non_generate_request_bypass_queue(self):
        """Test that non-generate requests bypass the queue."""
        # Set up mock return
        self.mock_schema_manager.get_all_schema_names.return_value = ["schema1", "schema2"]
        
        # Start the request processor
        await self.request_processor.start()
        
        try:
            # Process a get_schemas request (should bypass queue)
            response = await self.request_processor.process_request({
                "request_type": "get_schemas"
            })
            
            # Check that the response is as expected
            assert response["status"] == "success"
            assert "data" in response
            assert "schemas" in response["data"]
            assert response["data"]["schemas"] == ["schema1", "schema2"]
            
            # Check that the schema manager was called correctly
            self.mock_schema_manager.get_all_schema_names.assert_called_once()
            
            # Check queue metrics (should show no processed requests)
            metrics = self.request_processor.get_queue_metrics()
            assert metrics["processed_requests"] == 0
        finally:
            # Stop the request processor
            await self.request_processor.stop()
    
    @pytest.mark.asyncio
    async def test_process_generate_request_with_queue(self):
        """Test processing a generate request with queuing."""
        # Set up mock returns
        mock_schema = MagicMock()
        mock_schema.system_prompt = "You are a test assistant."
        self.mock_schema_manager.get_schema.return_value = mock_schema
        
        self.mock_model_manager.generate_response.return_value = '{"result": "test"}'
        self.mock_response_processor.process_response.return_value = {"result": "test"}
        
        # Start the request processor
        await self.request_processor.start()
        
        try:
            # Process a generate_response request
            response = await self.request_processor.process_request({
                "request_type": "generate_response",
                "query": "Test query",
                "schema": "test_schema",
                "parameters": {"temperature": 0.7}
            }, "test_request_id")
            
            # Check that the response is as expected
            assert response["status"] == "success"
            assert "data" in response
            assert response["data"] == {"result": "test"}
            assert "metadata" in response
            assert "model" in response["metadata"]
            assert "processing_time" in response["metadata"]
            assert "queue_wait_time" in response["metadata"]
            
            # Check that the dependencies were called correctly
            self.mock_schema_manager.get_schema.assert_called_once_with("test_schema")
            self.mock_model_manager.generate_response.assert_called_once()
            self.mock_response_processor.process_response.assert_called_once_with(
                '{"result": "test"}', "test_schema"
            )
            
            # Check queue metrics
            metrics = self.request_processor.get_queue_metrics()
            assert metrics["processed_requests"] == 1
            assert metrics["total_requests"] == 1
        finally:
            # Stop the request processor
            await self.request_processor.stop()
    
    @pytest.mark.asyncio
    async def test_queue_full(self):
        """Test behavior when the queue is full."""
        # Create a request processor with a very small queue
        request_processor = RequestProcessor(
            model_manager=self.mock_model_manager,
            schema_manager=self.mock_schema_manager,
            response_processor=self.mock_response_processor,
            rate_limit=1.0,  # Very slow processing
            rate_period=10.0,
            max_queue_size=1,  # Only one request in queue
            enable_queue=True
        )
        
        # Set up mock returns
        mock_schema = MagicMock()
        mock_schema.system_prompt = "You are a test assistant."
        self.mock_schema_manager.get_schema.return_value = mock_schema
        
        # Make model_manager.generate_response slow
        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate slow processing
            return '{"result": "test"}'
        
        self.mock_model_manager.generate_response.side_effect = slow_generate
        self.mock_response_processor.process_response.return_value = {"result": "test"}
        
        # Start the request processor
        await request_processor.start()
        
        try:
            # Submit first request (should be accepted)
            task1 = asyncio.create_task(
                request_processor.process_request({
                    "request_type": "generate_response",
                    "query": "Test query 1",
                    "schema": "test_schema"
                }, "request1")
            )
            
            # Give it a moment to be queued
            await asyncio.sleep(0.1)
            
            # Submit second request (should be accepted into queue)
            task2 = asyncio.create_task(
                request_processor.process_request({
                    "request_type": "generate_response",
                    "query": "Test query 2",
                    "schema": "test_schema"
                }, "request2")
            )
            
            # Give it a moment to be queued
            await asyncio.sleep(0.1)
            
            # Submit third request (should be rejected due to full queue)
            with pytest.raises(QueueFullError):
                await request_processor.process_request({
                    "request_type": "generate_response",
                    "query": "Test query 3",
                    "schema": "test_schema"
                }, "request3")
            
            # Wait for the first two requests to complete
            await task1
            await task2
            
            # Check queue metrics
            metrics = request_processor.get_queue_metrics()
            assert metrics["rejected_requests"] == 1
            assert metrics["processed_requests"] == 2
            assert metrics["total_requests"] == 2
        finally:
            # Stop the request processor
            await request_processor.stop()
            
            # Cancel any pending tasks
            if not task1.done():
                task1.cancel()
            if not task2.done():
                task2.cancel()
    
    @pytest.mark.asyncio
    async def test_queue_disabled(self):
        """Test behavior when queuing is disabled."""
        # Create a request processor with queuing disabled
        request_processor = RequestProcessor(
            model_manager=self.mock_model_manager,
            schema_manager=self.mock_schema_manager,
            response_processor=self.mock_response_processor,
            enable_queue=False
        )
        
        # Set up mock returns
        mock_schema = MagicMock()
        mock_schema.system_prompt = "You are a test assistant."
        self.mock_schema_manager.get_schema.return_value = mock_schema
        
        self.mock_model_manager.generate_response.return_value = '{"result": "test"}'
        self.mock_response_processor.process_response.return_value = {"result": "test"}
        
        # Start the request processor
        await request_processor.start()
        
        try:
            # Process a generate_response request
            response = await request_processor.process_request({
                "request_type": "generate_response",
                "query": "Test query",
                "schema": "test_schema"
            })
            
            # Check that the response is as expected
            assert response["status"] == "success"
            assert "data" in response
            assert response["data"] == {"result": "test"}
            
            # Check that the dependencies were called correctly
            self.mock_schema_manager.get_schema.assert_called_once_with("test_schema")
            self.mock_model_manager.generate_response.assert_called_once()
            self.mock_response_processor.process_response.assert_called_once_with(
                '{"result": "test"}', "test_schema"
            )
            
            # Check queue metrics
            metrics = request_processor.get_queue_metrics()
            assert metrics == {"queue_enabled": False}
        finally:
            # Stop the request processor
            await request_processor.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        # Set up mock returns
        mock_schema = MagicMock()
        mock_schema.system_prompt = "You are a test assistant."
        self.mock_schema_manager.get_schema.return_value = mock_schema
        
        # Make model_manager.generate_response return different results based on input
        async def generate_response(prompt, parameters):
            query = prompt.split("\n\n")[-1]
            return f'{{"result": "{query}"}}'
        
        self.mock_model_manager.generate_response.side_effect = generate_response
        
        # Make response_processor.process_response return the input
        async def process_response(raw_response, schema_name):
            import json
            return json.loads(raw_response)
        
        self.mock_response_processor.process_response.side_effect = process_response
        
        # Start the request processor
        await self.request_processor.start()
        
        try:
            # Submit multiple requests concurrently
            tasks = []
            for i in range(5):
                tasks.append(
                    asyncio.create_task(
                        self.request_processor.process_request({
                            "request_type": "generate_response",
                            "query": f"Query {i}",
                            "schema": "test_schema"
                        }, f"request{i}")
                    )
                )
            
            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks)
            
            # Check that all responses are correct
            for i, response in enumerate(responses):
                assert response["status"] == "success"
                assert response["data"]["result"] == f"Query {i}"
                assert "queue_wait_time" in response["metadata"]
            
            # Check queue metrics
            metrics = self.request_processor.get_queue_metrics()
            assert metrics["processed_requests"] == 5
            assert metrics["total_requests"] == 5
        finally:
            # Stop the request processor
            await self.request_processor.stop()