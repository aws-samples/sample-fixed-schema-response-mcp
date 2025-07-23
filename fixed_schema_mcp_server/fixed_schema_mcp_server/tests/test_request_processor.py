"""
Tests for the request processor module.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from fixed_schema_mcp_server.core.request_processor import RequestProcessor
from fixed_schema_mcp_server.core.exceptions import RequestValidationError, RequestProcessingError
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError
from fixed_schema_mcp_server.core.request_queue import QueueFullError


class TestRequestProcessor:
    """Test cases for the RequestProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.mock_model_manager = MagicMock()
        self.mock_schema_manager = MagicMock()
        self.mock_response_processor = MagicMock()
        
        # Configure the mock model manager
        self.mock_model_manager.generate_response = AsyncMock(return_value='{"name": "John Doe", "age": 30, "email": "john@example.com"}')
        
        # Configure the mock schema manager
        self.mock_schema_manager.get_schema.return_value = MagicMock(
            system_prompt="You are a test assistant.",
            schema=MagicMock()
        )
        
        # Configure the mock response processor
        self.mock_response_processor.process_response = AsyncMock(return_value={
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        })
        
        # Create the request processor with queue disabled for most tests
        self.request_processor = RequestProcessor(
            model_manager=self.mock_model_manager,
            schema_manager=self.mock_schema_manager,
            response_processor=self.mock_response_processor,
            enable_queue=False
        )
    
    @pytest.mark.asyncio
    async def test_process_request_generate_response(self):
        """Test processing a generate_response request."""
        # Create a generate_response request
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe",
            "schema": "test_schema",
            "parameters": {"temperature": 0.7}
        }
        
        # Process the request
        result = await self.request_processor.process_request(request, "test-request-id")
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
        assert "metadata" in result
        
        # Verify the model manager was called with the correct parameters
        self.mock_model_manager.generate_response.assert_called_once()
        args, kwargs = self.mock_model_manager.generate_response.call_args
        assert "Tell me about John Doe" in args[0]
        assert kwargs.get("parameters") == {"temperature": 0.7}
        
        # Verify the response processor was called with the correct parameters
        self.mock_response_processor.process_response.assert_called_once()
        args, kwargs = self.mock_response_processor.process_response.call_args
        assert args[1] == "test_schema"
    
    @pytest.mark.asyncio
    async def test_process_request_get_schemas(self):
        """Test processing a get_schemas request."""
        # Configure the mock schema manager
        self.mock_schema_manager.get_all_schema_names.return_value = ["schema1", "schema2", "schema3"]
        
        # Create a get_schemas request
        request = {
            "request_type": "get_schemas"
        }
        
        # Process the request
        result = await self.request_processor.process_request(request)
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
        assert "schemas" in result["data"]
        assert result["data"]["schemas"] == ["schema1", "schema2", "schema3"]
        
        # Verify the schema manager was called
        self.mock_schema_manager.get_all_schema_names.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_get_schema(self):
        """Test processing a get_schema request."""
        # Configure the mock schema manager
        mock_schema = MagicMock()
        mock_schema.model_dump.return_value = {
            "name": "test_schema",
            "description": "A test schema",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            }
        }
        self.mock_schema_manager.get_schema.return_value = mock_schema
        
        # Create a get_schema request
        request = {
            "request_type": "get_schema",
            "schema_name": "test_schema"
        }
        
        # Process the request
        result = await self.request_processor.process_request(request)
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
        assert "schema" in result["data"]
        
        # Verify the schema manager was called with the correct parameters
        self.mock_schema_manager.get_schema.assert_called_once_with("test_schema")
    
    @pytest.mark.asyncio
    async def test_process_request_invalid_request_type(self):
        """Test processing a request with an invalid request type."""
        # Create a request with an invalid request type
        request = {
            "request_type": "invalid_type",
            "data": "some data"
        }
        
        # Process the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            await self.request_processor.process_request(request)
    
    @pytest.mark.asyncio
    async def test_process_request_missing_required_fields(self):
        """Test processing a request with missing required fields."""
        # Create a generate_response request missing required fields
        request = {
            "request_type": "generate_response",
            # Missing query and schema
            "parameters": {"temperature": 0.7}
        }
        
        # Process the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            await self.request_processor.process_request(request)
    
    @pytest.mark.asyncio
    async def test_process_request_schema_not_found(self):
        """Test processing a request with a non-existent schema."""
        # Configure the mock schema manager to raise SchemaNotFoundError
        self.mock_schema_manager.get_schema.side_effect = SchemaNotFoundError("Schema not found")
        
        # Create a generate_response request with a non-existent schema
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe",
            "schema": "nonexistent_schema"
        }
        
        # Process the request should raise SchemaNotFoundError
        with pytest.raises(SchemaNotFoundError):
            await self.request_processor.process_request(request)
    
    @pytest.mark.asyncio
    async def test_process_request_with_queue(self):
        """Test processing a request with the queue enabled."""
        # Create a request processor with queue enabled
        request_processor_with_queue = RequestProcessor(
            model_manager=self.mock_model_manager,
            schema_manager=self.mock_schema_manager,
            response_processor=self.mock_response_processor,
            enable_queue=True
        )
        
        # Mock the request queue
        mock_queue = MagicMock()
        mock_queue.enqueue = AsyncMock(return_value={
            "request_data": {
                "request_type": "generate_response",
                "query": "Tell me about John Doe",
                "schema": "test_schema"
            },
            "wait_time": 0.5,
            "queue_position": 1
        })
        request_processor_with_queue._request_queue = mock_queue
        
        # Start the request processor
        await request_processor_with_queue.start()
        
        try:
            # Create a generate_response request
            request = {
                "request_type": "generate_response",
                "query": "Tell me about John Doe",
                "schema": "test_schema"
            }
            
            # Process the request
            result = await request_processor_with_queue.process_request(request, "test-request-id")
            
            # Verify the result
            assert result["status"] == "success"
            assert "data" in result
            assert "metadata" in result
            assert "queue_wait_time" in result["metadata"]
            assert "queue_position" in result["metadata"]
            
            # Verify the queue was used
            mock_queue.enqueue.assert_called_once()
        finally:
            # Stop the request processor
            await request_processor_with_queue.stop()
    
    @pytest.mark.asyncio
    async def test_process_request_queue_full(self):
        """Test processing a request when the queue is full."""
        # Create a request processor with queue enabled
        request_processor_with_queue = RequestProcessor(
            model_manager=self.mock_model_manager,
            schema_manager=self.mock_schema_manager,
            response_processor=self.mock_response_processor,
            enable_queue=True
        )
        
        # Mock the request queue to raise QueueFullError
        mock_queue = MagicMock()
        mock_queue.enqueue = AsyncMock(side_effect=QueueFullError("Queue is full"))
        request_processor_with_queue._request_queue = mock_queue
        
        # Start the request processor
        await request_processor_with_queue.start()
        
        try:
            # Create a generate_response request
            request = {
                "request_type": "generate_response",
                "query": "Tell me about John Doe",
                "schema": "test_schema"
            }
            
            # Process the request should raise QueueFullError
            with pytest.raises(QueueFullError):
                await request_processor_with_queue.process_request(request)
        finally:
            # Stop the request processor
            await request_processor_with_queue.stop()
    
    @pytest.mark.asyncio
    async def test_get_queue_metrics(self):
        """Test getting queue metrics."""
        # Create a request processor with queue enabled
        request_processor_with_queue = RequestProcessor(
            model_manager=self.mock_model_manager,
            schema_manager=self.mock_schema_manager,
            response_processor=self.mock_response_processor,
            enable_queue=True
        )
        
        # Mock the request queue
        mock_queue = MagicMock()
        mock_queue.get_metrics.return_value = {
            "queue_size": 0,
            "processed_requests": 0,
            "average_wait_time": 0.0,
            "average_processing_time": 0.0
        }
        request_processor_with_queue._request_queue = mock_queue
        
        # Get queue metrics
        metrics = request_processor_with_queue.get_queue_metrics()
        
        # Verify the metrics
        assert "queue_size" in metrics
        assert "processed_requests" in metrics
        assert "average_wait_time" in metrics
        assert "average_processing_time" in metrics
        
        # Verify the queue was used
        mock_queue.get_metrics.assert_called_once()
    
    def test_validate_request_valid(self):
        """Test validating a valid request."""
        # Create a valid generate_response request
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe",
            "schema": "test_schema",
            "parameters": {"temperature": 0.7}
        }
        
        # Validate the request
        self.request_processor._validate_request(request)
        # No exception should be raised
    
    def test_validate_request_invalid_type(self):
        """Test validating a request with an invalid type."""
        # Create a request with an invalid type
        request = "This is not a dictionary"
        
        # Validate the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            self.request_processor._validate_request(request)
    
    def test_validate_request_missing_request_type(self):
        """Test validating a request with a missing request type."""
        # Create a request with a missing request type
        request = {
            "query": "Tell me about John Doe",
            "schema": "test_schema"
        }
        
        # Validate the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            self.request_processor._validate_request(request)
    
    def test_validate_generate_response_request_valid(self):
        """Test validating a valid generate_response request."""
        # Create a valid generate_response request
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe",
            "schema": "test_schema",
            "parameters": {"temperature": 0.7}
        }
        
        # Validate the request
        self.request_processor._validate_generate_response_request(request)
        # No exception should be raised
    
    def test_validate_generate_response_request_missing_query(self):
        """Test validating a generate_response request with a missing query."""
        # Create a generate_response request with a missing query
        request = {
            "request_type": "generate_response",
            "schema": "test_schema"
        }
        
        # Validate the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            self.request_processor._validate_generate_response_request(request)
    
    def test_validate_generate_response_request_missing_schema(self):
        """Test validating a generate_response request with a missing schema."""
        # Create a generate_response request with a missing schema
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe"
        }
        
        # Validate the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            self.request_processor._validate_generate_response_request(request)
    
    def test_validate_generate_response_request_invalid_parameters(self):
        """Test validating a generate_response request with invalid parameters."""
        # Create a generate_response request with invalid parameters
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe",
            "schema": "test_schema",
            "parameters": "invalid parameters"  # Should be a dictionary
        }
        
        # Validate the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            self.request_processor._validate_generate_response_request(request)
    
    def test_validate_get_schema_request_valid(self):
        """Test validating a valid get_schema request."""
        # Create a valid get_schema request
        request = {
            "request_type": "get_schema",
            "schema_name": "test_schema"
        }
        
        # Validate the request
        self.request_processor._validate_get_schema_request(request)
        # No exception should be raised
    
    def test_validate_get_schema_request_missing_schema_name(self):
        """Test validating a get_schema request with a missing schema name."""
        # Create a get_schema request with a missing schema name
        request = {
            "request_type": "get_schema"
        }
        
        # Validate the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            self.request_processor._validate_get_schema_request(request)
    
    def test_validate_get_schema_request_invalid_schema_name(self):
        """Test validating a get_schema request with an invalid schema name."""
        # Create a get_schema request with an invalid schema name
        request = {
            "request_type": "get_schema",
            "schema_name": 123  # Should be a string
        }
        
        # Validate the request should raise RequestValidationError
        with pytest.raises(RequestValidationError):
            self.request_processor._validate_get_schema_request(request)