"""
Tests for the MCP server module.
"""

import os
import json
import pytest
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock

from fixed_schema_mcp_server.core.server import MCPServer
from fixed_schema_mcp_server.core.exceptions import MCPServerError, MCPLifecycleError, MCPRequestError
from fixed_schema_mcp_server.core.request_queue import QueueFullError
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError


class TestMCPServer:
    """Test cases for the MCPServer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test configuration
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.json")
        
        # Create a test configuration file
        self.test_config = {
            "server": {
                "host": "localhost",
                "port": 8000,
                "log_level": "info"
            },
            "model": {
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "test_api_key",
                "parameters": {
                    "temperature": 0.7,
                    "top_p": 1.0,
                    "max_tokens": 1000
                }
            },
            "schemas": {
                "path": self.temp_dir.name,
                "default_schema": "default"
            },
            "error_handling": {
                "max_retries": 3,
                "enable_monitoring": True
            },
            "performance": {
                "rate_limit": 10.0,
                "rate_period": 60.0,
                "burst_limit": None,
                "max_queue_size": 100,
                "enable_queue": True
            }
        }
        
        with open(self.config_path, "w") as f:
            json.dump(self.test_config, f)
        
        # Create a test schema file
        self.test_schema = {
            "name": "test_schema",
            "description": "A test schema",
            "schema": {
                "type": "object",
                "required": ["name", "age"],
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0},
                    "email": {"type": "string", "format": "email"}
                }
            },
            "system_prompt": "You are a test assistant."
        }
        
        with open(os.path.join(self.temp_dir.name, "test_schema.json"), "w") as f:
            json.dump(self.test_schema, f)
        
        # Create mock dependencies
        self.mock_protocol_handler = MagicMock()
        self.mock_protocol_handler.initialize = AsyncMock()
        self.mock_protocol_handler.start = AsyncMock()
        self.mock_protocol_handler.stop = AsyncMock()
        
        self.mock_config_manager = MagicMock()
        self.mock_config_manager.load_config.return_value = self.test_config
        
        self.mock_schema_manager = MagicMock()
        self.mock_schema_manager.load_schemas = MagicMock()
        self.mock_schema_manager.get_schema_count.return_value = 1
        
        self.mock_model_manager = MagicMock()
        self.mock_model_manager.start = AsyncMock()
        self.mock_model_manager.stop = AsyncMock()
        
        self.mock_request_processor = MagicMock()
        self.mock_request_processor.start = AsyncMock()
        self.mock_request_processor.stop = AsyncMock()
        self.mock_request_processor.process_request = AsyncMock(return_value={
            "status": "success",
            "data": {"name": "John Doe", "age": 30, "email": "john@example.com"}
        })
        
        # Patch the dependencies
        self.patches = [
            patch("fixed_schema_mcp_server.core.server.MCPProtocolHandler", return_value=self.mock_protocol_handler),
            patch("fixed_schema_mcp_server.core.server.ConfigManager", return_value=self.mock_config_manager),
            patch("fixed_schema_mcp_server.core.server.SchemaManager", return_value=self.mock_schema_manager),
            patch("fixed_schema_mcp_server.core.server.ModelManager", return_value=self.mock_model_manager),
            patch("fixed_schema_mcp_server.core.server.RequestProcessor", return_value=self.mock_request_processor),
            patch("fixed_schema_mcp_server.core.server.ErrorHandler", return_value=MagicMock()),
            patch("fixed_schema_mcp_server.core.server.ResponseProcessor", return_value=MagicMock())
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Tear down test fixtures."""
        # Stop all patches
        for p in self.patches:
            p.stop()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Test initializing the MCP server."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Verify the server was initialized correctly
        assert server._config_path == self.config_path
        assert server._config == self.test_config
        assert server._running is False
        
        # Verify the dependencies were initialized
        self.mock_config_manager.load_config.assert_called_once_with(self.config_path)
        self.mock_schema_manager.load_schemas.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start(self):
        """Test starting the MCP server."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Start the server
        await server.start()
        
        # Verify the server was started correctly
        assert server._running is True
        
        # Verify the dependencies were started
        self.mock_protocol_handler.initialize.assert_called_once()
        self.mock_protocol_handler.start.assert_called_once()
        self.mock_model_manager.start.assert_called_once()
        self.mock_request_processor.start.assert_called_once()
        
        # Stop the server to clean up
        await server.stop()
    
    @pytest.mark.asyncio
    async def test_stop(self):
        """Test stopping the MCP server."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Start the server
        await server.start()
        
        # Stop the server
        await server.stop()
        
        # Verify the server was stopped correctly
        assert server._running is False
        
        # Verify the dependencies were stopped
        self.mock_protocol_handler.stop.assert_called_once()
        self.mock_model_manager.stop.assert_called_once()
        self.mock_request_processor.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_request(self):
        """Test handling a request."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {
                "request_type": "generate_response",
                "query": "Tell me about John Doe",
                "schema": "test_schema",
                "id": "test-request-id"
            }
            
            # Handle the request
            response = await server.handle_request(request)
            
            # Verify the response
            assert response["status"] == "success"
            assert "data" in response
            
            # Verify the request processor was called
            self.mock_request_processor.process_request.assert_called_once_with(request, "test-request-id")
        finally:
            # Stop the server
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_handle_request_server_not_running(self):
        """Test handling a request when the server is not running."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Create a test request
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe",
            "schema": "test_schema"
        }
        
        # Handle the request
        response = await server.handle_request(request)
        
        # Verify the response
        assert response["status"] == "error"
        assert "error" in response
        assert response["error"]["code"] == "server_not_running"
    
    @pytest.mark.asyncio
    async def test_handle_request_queue_full(self):
        """Test handling a request when the queue is full."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the request processor to raise QueueFullError
        self.mock_request_processor.process_request.side_effect = QueueFullError("Queue is full")
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {
                "request_type": "generate_response",
                "query": "Tell me about John Doe",
                "schema": "test_schema"
            }
            
            # Handle the request
            response = await server.handle_request(request)
            
            # Verify the response
            assert response["status"] == "error"
            assert "error" in response
            assert response["error"]["code"] == "queue_full"
        finally:
            # Stop the server
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_handle_request_schema_not_found(self):
        """Test handling a request with a non-existent schema."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the request processor to raise SchemaNotFoundError
        self.mock_request_processor.process_request.side_effect = SchemaNotFoundError("Schema not found")
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {
                "request_type": "generate_response",
                "query": "Tell me about John Doe",
                "schema": "nonexistent_schema"
            }
            
            # Handle the request
            response = await server.handle_request(request)
            
            # Verify the response
            assert response["status"] == "error"
            assert "error" in response
        finally:
            # Stop the server
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_process_request_with_retry(self):
        """Test processing a request with retry logic."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the request processor to fail once then succeed
        self.mock_request_processor.process_request.side_effect = [
            Exception("Temporary error"),
            {"status": "success", "data": {"name": "John Doe", "age": 30, "email": "john@example.com"}}
        ]
        
        # Configure the error handler to retry
        server._error_handler.should_retry = MagicMock(return_value=True)
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {
                "request_type": "generate_response",
                "query": "Tell me about John Doe",
                "schema": "test_schema"
            }
            
            # Process the request
            response = await server._process_request_with_retry(request)
            
            # Verify the response
            assert response["status"] == "success"
            assert "data" in response
            
            # Verify the request processor was called twice
            assert self.mock_request_processor.process_request.call_count == 2
        finally:
            # Stop the server
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_handle_generate_request(self):
        """Test handling a generate request."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the model manager
        self.mock_model_manager.generate_response = AsyncMock(return_value='{"name": "John Doe", "age": 30, "email": "john@example.com"}')
        self.mock_model_manager.get_model_info = MagicMock(return_value={"model": "gpt-4"})
        
        # Configure the response processor
        response_processor = MagicMock()
        response_processor.process_response = AsyncMock(return_value={
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        })
        server._response_processor = response_processor
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {
                "query": "Tell me about John Doe",
                "schema": "test_schema",
                "parameters": {"temperature": 0.7}
            }
            
            # Handle the request
            response = await server._handle_generate_request(request)
            
            # Verify the response
            assert response["status"] == "success"
            assert "data" in response
            assert "metadata" in response
            assert response["metadata"]["model"] == "gpt-4"
            
            # Verify the model manager was called
            self.mock_model_manager.generate_response.assert_called_once()
            
            # Verify the response processor was called
            response_processor.process_response.assert_called_once()
        finally:
            # Stop the server
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_handle_validate_request(self):
        """Test handling a validate request."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the schema manager
        self.mock_schema_manager.validate_against_schema.return_value = True
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {
                "data": {"name": "John Doe", "age": 30, "email": "john@example.com"},
                "schema": "test_schema"
            }
            
            # Handle the request
            response = await server._handle_validate_request(request)
            
            # Verify the response
            assert response["status"] == "success"
            assert response["valid"] is True
            assert response["errors"] is None
            
            # Verify the schema manager was called
            self.mock_schema_manager.validate_against_schema.assert_called_once_with(request["data"], "test_schema")
        finally:
            # Stop the server
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_handle_list_schemas_request(self):
        """Test handling a list_schemas request."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the schema manager
        self.mock_schema_manager.get_all_schema_names.return_value = ["schema1", "schema2", "schema3"]
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {}
            
            # Handle the request
            response = await server._handle_list_schemas_request(request)
            
            # Verify the response
            assert response["status"] == "success"
            assert "schemas" in response
            assert response["schemas"] == ["schema1", "schema2", "schema3"]
            
            # Verify the schema manager was called
            self.mock_schema_manager.get_all_schema_names.assert_called_once()
        finally:
            # Stop the server
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_handle_get_schema_request(self):
        """Test handling a get_schema request."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the schema manager
        mock_schema = MagicMock()
        mock_schema.name = "test_schema"
        mock_schema.description = "A test schema"
        mock_schema.schema = MagicMock()
        mock_schema.schema.dict = MagicMock(return_value={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        })
        mock_schema.system_prompt = "You are a test assistant."
        self.mock_schema_manager.get_schema.return_value = mock_schema
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {
                "name": "test_schema"
            }
            
            # Handle the request
            response = await server._handle_get_schema_request(request)
            
            # Verify the response
            assert response["status"] == "success"
            assert "schema" in response
            assert response["schema"]["name"] == "test_schema"
            assert response["schema"]["description"] == "A test schema"
            assert "schema" in response["schema"]
            assert response["schema"]["system_prompt"] == "You are a test assistant."
            
            # Verify the schema manager was called
            self.mock_schema_manager.get_schema.assert_called_once_with("test_schema")
        finally:
            # Stop the server
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_handle_health_request(self):
        """Test handling a health request."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the model manager
        self.mock_model_manager.check_model_health = AsyncMock(return_value={
            "status": "healthy",
            "latency": 0.1
        })
        
        # Start the server
        await server.start()
        
        try:
            # Create a test request
            request = {}
            
            # Handle the request
            response = await server._handle_health_request(request)
            
            # Verify the response
            assert response["status"] == "success"
            assert "health" in response
            assert "server" in response["health"]
            assert "model" in response["health"]
            assert response["health"]["server"]["status"] == "healthy"
            assert response["health"]["model"]["status"] == "healthy"
            
            # Verify the model manager was called
            self.mock_model_manager.check_model_health.assert_called_once()
        finally:
            # Stop the server
            await server.stop()
    
    def test_is_running(self):
        """Test the is_running property."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Check initial state
        assert server.is_running is False
        
        # Set running state
        server._running = True
        
        # Check updated state
        assert server.is_running is True
    
    def test_get_error_monitoring_data(self):
        """Test getting error monitoring data."""
        # Create the server
        server = MCPServer(self.config_path)
        
        # Configure the error handler
        server._error_handler.get_monitoring_data = MagicMock(return_value={
            "total_errors": 0,
            "error_rate": 0.0,
            "error_types": {}
        })
        
        # Get error monitoring data
        data = server.get_error_monitoring_data()
        
        # Verify the data
        assert "total_errors" in data
        assert "error_rate" in data
        assert "error_types" in data
        
        # Verify the error handler was called
        server._error_handler.get_monitoring_data.assert_called_once()