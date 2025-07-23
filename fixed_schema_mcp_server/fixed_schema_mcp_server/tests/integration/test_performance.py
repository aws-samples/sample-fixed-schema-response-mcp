"""
Performance tests for the Fixed Schema Response MCP Server.
"""

import os
import json
import time
import asyncio
import tempfile
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from fixed_schema_mcp_server.core.server import MCPServer
from fixed_schema_mcp_server.core.request_processor import RequestProcessor


class TestPerformance:
    """Performance tests for the MCP server."""
    
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
                "default_schema": "test"
            },
            "error_handling": {
                "max_retries": 3,
                "enable_monitoring": True
            },
            "performance": {
                "rate_limit": 100.0,  # High rate limit for performance testing
                "rate_period": 60.0,
                "burst_limit": None,
                "max_queue_size": 1000,  # Large queue for performance testing
                "enable_queue": True
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(test_config, f)
        
        # Create a test schema file
        test_schema = {
            "name": "test",
            "description": "A test schema",
            "schema": {
                "type": "object",
                "required": ["name", "value"],
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "integer"}
                }
            },
            "system_prompt": "You are a test assistant."
        }
        
        with open(os.path.join(schema_path, "test.json"), "w") as f:
            json.dump(test_schema, f)
        
        # Mock the model manager to return responses with controlled latency
        with patch("fixed_schema_mcp_server.model.model_manager.ModelManager.generate_response") as mock_generate:
            # Configure the mock to return responses with a small delay
            async def mock_generate_response(prompt, parameters=None):
                # Simulate model latency (10-20ms)
                await asyncio.sleep(0.01 + (0.01 * (parameters.get("temperature", 0.5) if parameters else 0.5)))
                return json.dumps({"name": "Test", "value": 42})
            
            mock_generate.side_effect = mock_generate_response
            
            # Create and start the server
            server = MCPServer(config_path)
            await server.start()
            
            yield server, temp_dir
            
            # Stop the server and clean up
            await server.stop()
            temp_dir.cleanup()
    
    @pytest.mark.asyncio
    async def test_request_throughput(self, server_setup):
        """Test the request throughput of the server."""
        server, _ = await server_setup
        
        # Number of requests to send
        num_requests = 50
        
        # Create a test request
        request = {
            "request_type": "generate_response",
            "query": "Test query",
            "schema": "test",
            "parameters": {"temperature": 0.5}
        }
        
        # Send requests concurrently and measure time
        start_time = time.time()
        
        tasks = []
        for i in range(num_requests):
            # Create a unique request ID
            request_id = f"test-request-{i}"
            # Create a task for each request
            tasks.append(server.handle_request({**request, "id": request_id}))
        
        # Wait for all requests to complete
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        throughput = num_requests / total_time
        
        # Verify all responses were successful
        assert all(response["status"] == "success" for response in responses)
        
        # Log performance metrics
        print(f"\nPerformance test results:")
        print(f"Total requests: {num_requests}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Throughput: {throughput:.2f} requests/second")
        
        # Get queue metrics
        queue_metrics = server._request_processor.get_queue_metrics()
        print(f"Queue metrics: {queue_metrics}")
        
        # Assert minimum throughput (adjust based on your requirements)
        # This is a very conservative estimate since we're using mocks
        assert throughput > 10.0, f"Throughput too low: {throughput:.2f} requests/second"
    
    @pytest.mark.asyncio
    async def test_response_latency(self, server_setup):
        """Test the response latency of the server."""
        server, _ = await server_setup
        
        # Number of requests to send
        num_requests = 20
        
        # Create a test request
        request = {
            "request_type": "generate_response",
            "query": "Test query",
            "schema": "test",
            "parameters": {"temperature": 0.5}
        }
        
        # Send requests and measure latency
        latencies = []
        
        for i in range(num_requests):
            # Create a unique request ID
            request_id = f"test-request-{i}"
            
            # Measure request latency
            start_time = time.time()
            response = await server.handle_request({**request, "id": request_id})
            end_time = time.time()
            
            # Calculate latency
            latency = end_time - start_time
            latencies.append(latency)
            
            # Verify the response was successful
            assert response["status"] == "success"
            
            # Add a small delay between requests
            await asyncio.sleep(0.01)
        
        # Calculate average and percentile latencies
        avg_latency = sum(latencies) / len(latencies)
        latencies.sort()
        p50_latency = latencies[int(num_requests * 0.5)]
        p95_latency = latencies[int(num_requests * 0.95)]
        p99_latency = latencies[int(num_requests * 0.99)]
        
        # Log latency metrics
        print(f"\nLatency test results:")
        print(f"Average latency: {avg_latency:.3f} seconds")
        print(f"50th percentile latency: {p50_latency:.3f} seconds")
        print(f"95th percentile latency: {p95_latency:.3f} seconds")
        print(f"99th percentile latency: {p99_latency:.3f} seconds")
        
        # Assert maximum average latency (adjust based on your requirements)
        # This is a very conservative estimate since we're using mocks
        assert avg_latency < 0.5, f"Average latency too high: {avg_latency:.3f} seconds"
    
    @pytest.mark.asyncio
    async def test_queue_behavior(self, server_setup):
        """Test the behavior of the request queue under load."""
        server, _ = await server_setup
        
        # Get the request processor
        request_processor = server._request_processor
        
        # Enable queue with a low rate limit for testing
        request_processor._enable_queue = True
        request_processor._request_queue._rate_limit = 5.0  # 5 requests per second
        
        # Number of requests to send
        num_requests = 20
        
        # Create a test request
        request = {
            "request_type": "generate_response",
            "query": "Test query",
            "schema": "test",
            "parameters": {"temperature": 0.5}
        }
        
        # Send requests concurrently
        tasks = []
        for i in range(num_requests):
            # Create a unique request ID
            request_id = f"test-request-{i}"
            # Create a task for each request
            tasks.append(server.handle_request({**request, "id": request_id}))
        
        # Wait for all requests to complete
        responses = await asyncio.gather(*tasks)
        
        # Get queue metrics
        queue_metrics = request_processor.get_queue_metrics()
        
        # Log queue metrics
        print(f"\nQueue test results:")
        print(f"Queue metrics: {queue_metrics}")
        
        # Verify all responses were successful
        assert all(response["status"] == "success" for response in responses)
        
        # Verify queue was used
        assert queue_metrics["processed_requests"] >= num_requests
        
        # Verify average wait time is reasonable
        assert "average_wait_time" in queue_metrics
        
        # Check that some requests had to wait in the queue
        # This is expected due to the rate limiting
        assert queue_metrics["average_wait_time"] > 0.0
    
    @pytest.mark.asyncio
    async def test_concurrent_schema_requests(self, server_setup):
        """Test concurrent schema-related requests."""
        server, _ = await server_setup
        
        # Number of requests to send
        num_requests = 50
        
        # Create different types of requests
        requests = [
            {"request_type": "get_schemas"},
            {"request_type": "get_schema", "schema_name": "test"},
            {"request_type": "generate_response", "query": "Test query", "schema": "test"}
        ]
        
        # Send requests concurrently
        tasks = []
        for i in range(num_requests):
            # Select a request type based on index
            request = requests[i % len(requests)]
            # Create a unique request ID
            request_id = f"test-request-{i}"
            # Create a task for each request
            tasks.append(server.handle_request({**request, "id": request_id}))
        
        # Wait for all requests to complete
        responses = await asyncio.gather(*tasks)
        
        # Verify all responses were successful
        assert all(response["status"] == "success" for response in responses)
        
        # Count response types
        get_schemas_count = sum(1 for r in responses if "schemas" in r.get("data", {}))
        get_schema_count = sum(1 for r in responses if "schema" in r.get("data", {}))
        generate_count = sum(1 for r in responses if "name" in r.get("data", {}) and "value" in r.get("data", {}))
        
        # Log response counts
        print(f"\nConcurrent schema requests test results:")
        print(f"get_schemas responses: {get_schemas_count}")
        print(f"get_schema responses: {get_schema_count}")
        print(f"generate_response responses: {generate_count}")
        
        # Verify we got the expected number of each response type
        expected_get_schemas = num_requests // len(requests) + (1 if num_requests % len(requests) > 0 else 0)
        expected_get_schema = num_requests // len(requests) + (1 if num_requests % len(requests) > 1 else 0)
        expected_generate = num_requests // len(requests)
        
        assert abs(get_schemas_count - expected_get_schemas) <= 1
        assert abs(get_schema_count - expected_get_schema) <= 1
        assert abs(generate_count - expected_generate) <= 1