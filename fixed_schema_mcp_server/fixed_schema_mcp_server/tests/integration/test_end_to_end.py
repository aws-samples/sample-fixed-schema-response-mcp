"""
End-to-end integration tests for the Fixed Schema Response MCP Server.
"""

import os
import json
import asyncio
import tempfile
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from fixed_schema_mcp_server.core.server import MCPServer
from fixed_schema_mcp_server.model.model_manager import ModelManager
from fixed_schema_mcp_server.schema.schema_manager import SchemaManager
from fixed_schema_mcp_server.response.response_processor import ResponseProcessor


class TestEndToEnd:
    """End-to-end integration tests for the MCP server."""
    
    @pytest.fixture
    async def server_setup(self):
        """Set up a test server with mocked model responses."""
        # Create a temporary directory for test configuration and schemas
        temp_dir = tempfile.TemporaryDirectory()
        config_path = os.path.join(temp_dir.name, "config.json")
        schema_path = os.path.join(temp_dir.name, "schemas")
        os.makedirs(schema_path, exist_ok=True)
        
        # Create a test configuration file
        test_config = {
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
                "path": schema_path,
                "default_schema": "person"
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
                "enable_queue": False  # Disable queue for testing
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(test_config, f)
        
        # Create test schema files
        person_schema = {
            "name": "person",
            "description": "Schema for person information",
            "schema": {
                "type": "object",
                "required": ["name", "age", "email"],
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0},
                    "email": {"type": "string", "format": "email"},
                    "address": {
                        "type": "object",
                        "properties": {
                            "street": {"type": "string"},
                            "city": {"type": "string"},
                            "zipcode": {"type": "string"}
                        }
                    }
                }
            },
            "system_prompt": "You are a personal information assistant."
        }
        
        product_schema = {
            "name": "product",
            "description": "Schema for product information",
            "schema": {
                "type": "object",
                "required": ["name", "price", "category"],
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number", "minimum": 0},
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "features": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "system_prompt": "You are a product information assistant."
        }
        
        with open(os.path.join(schema_path, "person.json"), "w") as f:
            json.dump(person_schema, f)
        
        with open(os.path.join(schema_path, "product.json"), "w") as f:
            json.dump(product_schema, f)
        
        # Mock the model manager to return predefined responses
        mock_responses = {
            "person": {
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "zipcode": "12345"
                }
            },
            "product": {
                "name": "Smartphone X",
                "price": 999.99,
                "category": "Electronics",
                "description": "The latest smartphone with advanced features",
                "features": [
                    "5G connectivity",
                    "High-resolution camera",
                    "Long battery life"
                ]
            }
        }
        
        # Create patches for the model manager
        with patch("fixed_schema_mcp_server.model.model_manager.ModelManager.generate_response") as mock_generate:
            # Configure the mock to return different responses based on the schema
            async def mock_generate_response(prompt, parameters=None):
                if "person" in prompt.lower():
                    return json.dumps(mock_responses["person"])
                elif "product" in prompt.lower():
                    return json.dumps(mock_responses["product"])
                else:
                    return json.dumps({"error": "Unknown schema"})
            
            mock_generate.side_effect = mock_generate_response
            
            # Create and start the server
            server = MCPServer(config_path)
            await server.start()
            
            yield server, mock_responses, temp_dir
            
            # Stop the server and clean up
            await server.stop()
            temp_dir.cleanup()
    
    @pytest.mark.asyncio
    async def test_generate_response_person(self, server_setup):
        """Test generating a response with the person schema."""
        server, mock_responses, _ = await server_setup
        
        # Create a request for person information
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe",
            "schema": "person",
            "parameters": {"temperature": 0.5}
        }
        
        # Process the request
        response = await server.handle_request(request)
        
        # Verify the response
        assert response["status"] == "success"
        assert "data" in response
        assert response["data"]["name"] == "John Doe"
        assert response["data"]["age"] == 30
        assert response["data"]["email"] == "john@example.com"
        assert "address" in response["data"]
        assert response["data"]["address"]["city"] == "Anytown"
    
    @pytest.mark.asyncio
    async def test_generate_response_product(self, server_setup):
        """Test generating a response with the product schema."""
        server, mock_responses, _ = await server_setup
        
        # Create a request for product information
        request = {
            "request_type": "generate_response",
            "query": "Tell me about the latest smartphone",
            "schema": "product",
            "parameters": {"temperature": 0.5}
        }
        
        # Process the request
        response = await server.handle_request(request)
        
        # Verify the response
        assert response["status"] == "success"
        assert "data" in response
        assert response["data"]["name"] == "Smartphone X"
        assert response["data"]["price"] == 999.99
        assert response["data"]["category"] == "Electronics"
        assert "features" in response["data"]
        assert len(response["data"]["features"]) == 3
    
    @pytest.mark.asyncio
    async def test_get_schemas(self, server_setup):
        """Test getting all schemas."""
        server, _, _ = await server_setup
        
        # Create a request to get all schemas
        request = {
            "request_type": "get_schemas"
        }
        
        # Process the request
        response = await server.handle_request(request)
        
        # Verify the response
        assert response["status"] == "success"
        assert "data" in response
        assert "schemas" in response["data"]
        assert set(response["data"]["schemas"]) == {"person", "product"}
    
    @pytest.mark.asyncio
    async def test_get_schema(self, server_setup):
        """Test getting a specific schema."""
        server, _, _ = await server_setup
        
        # Create a request to get the person schema
        request = {
            "request_type": "get_schema",
            "schema_name": "person"
        }
        
        # Process the request
        response = await server.handle_request(request)
        
        # Verify the response
        assert response["status"] == "success"
        assert "data" in response
        assert "schema" in response["data"]
        assert response["data"]["schema"]["name"] == "person"
        assert "schema" in response["data"]["schema"]
        assert "properties" in response["data"]["schema"]["schema"]
        assert "name" in response["data"]["schema"]["schema"]["properties"]
    
    @pytest.mark.asyncio
    async def test_schema_not_found(self, server_setup):
        """Test handling a request with a non-existent schema."""
        server, _, _ = await server_setup
        
        # Create a request with a non-existent schema
        request = {
            "request_type": "generate_response",
            "query": "Tell me about John Doe",
            "schema": "nonexistent_schema"
        }
        
        # Process the request
        response = await server.handle_request(request)
        
        # Verify the response
        assert response["status"] == "error"
        assert "error" in response
        assert "schema_not_found" in response["error"]["code"] or "Schema not found" in response["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_invalid_request(self, server_setup):
        """Test handling an invalid request."""
        server, _, _ = await server_setup
        
        # Create an invalid request missing required fields
        request = {
            "request_type": "generate_response",
            # Missing query and schema
        }
        
        # Process the request
        response = await server.handle_request(request)
        
        # Verify the response
        assert response["status"] == "error"
        assert "error" in response