"""
Tests for the MCP protocol handler.
"""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from fixed_schema_mcp_server.core.protocol import MCPProtocolHandler
from fixed_schema_mcp_server.core.exceptions import MCPProtocolError, MCPConnectionError


@pytest.fixture
def protocol_handler():
    """Create a protocol handler for testing."""
    return MCPProtocolHandler()


@pytest.mark.asyncio
async def test_register_request_handler(protocol_handler):
    """Test registering a request handler."""
    # Create a mock handler
    mock_handler = AsyncMock()
    mock_handler.return_value = {"result": "success"}
    
    # Register the handler
    protocol_handler.register_request_handler("test_request", mock_handler)
    
    # Check that the handler was registered
    assert "test_request" in protocol_handler._request_handlers
    assert protocol_handler._request_handlers["test_request"] == mock_handler


@pytest.mark.asyncio
async def test_handle_request(protocol_handler):
    """Test handling a request."""
    # Create a mock handler
    mock_handler = AsyncMock()
    mock_handler.return_value = {"result": "success"}
    
    # Register the handler
    protocol_handler.register_request_handler("test_request", mock_handler)
    
    # Create a mock for _send_response
    protocol_handler._send_response = AsyncMock()
    
    # Create a request message
    request = {
        "type": "request",
        "id": "test-id",
        "data": {
            "request_type": "test_request",
            "param1": "value1"
        }
    }
    
    # Handle the request
    await protocol_handler._handle_message(request)
    
    # Check that the handler was called with the correct data
    mock_handler.assert_called_once_with(request["data"])
    
    # Check that _send_response was called with the correct data
    protocol_handler._send_response.assert_called_once_with(
        "test-id", 
        {"result": "success"}
    )


@pytest.mark.asyncio
async def test_handle_ping(protocol_handler):
    """Test handling a ping message."""
    # Create a mock for _send_message
    protocol_handler._send_message = AsyncMock()
    
    # Create a ping message
    ping = {
        "type": "ping",
        "id": "ping-id"
    }
    
    # Handle the ping
    await protocol_handler._handle_message(ping)
    
    # Check that _send_message was called with a pong response
    call_args = protocol_handler._send_message.call_args[0][0]
    assert call_args["type"] == "pong"
    assert call_args["id"] == "ping-id"


@pytest.mark.asyncio
async def test_handle_invalid_message(protocol_handler):
    """Test handling an invalid message."""
    # Create a mock for _send_error
    protocol_handler._send_error = AsyncMock()
    
    # Create an invalid message (missing type)
    invalid_message = {
        "id": "test-id",
        "data": {}
    }
    
    # Handle the message
    with pytest.raises(MCPProtocolError):
        await protocol_handler._handle_message(invalid_message)


@pytest.mark.asyncio
async def test_handle_invalid_request(protocol_handler):
    """Test handling an invalid request."""
    # Create a mock for _send_error
    protocol_handler._send_error = AsyncMock()
    
    # Create an invalid request (missing id)
    invalid_request = {
        "type": "request",
        "data": {
            "request_type": "test_request"
        }
    }
    
    # Handle the request
    with pytest.raises(MCPProtocolError):
        await protocol_handler._handle_request(invalid_request)


@pytest.mark.asyncio
async def test_handle_unsupported_request_type(protocol_handler):
    """Test handling a request with an unsupported request type."""
    # Create a mock for _send_error
    protocol_handler._send_error = AsyncMock()
    
    # Create a request with an unsupported request type
    request = {
        "type": "request",
        "id": "test-id",
        "data": {
            "request_type": "unsupported_request"
        }
    }
    
    # Handle the request
    await protocol_handler._handle_message(request)
    
    # Check that _send_error was called with the correct data
    protocol_handler._send_error.assert_called_once_with(
        "unsupported_request_type",
        "Unsupported request type: unsupported_request",
        "test-id"
    )


@pytest.mark.asyncio
async def test_send_response(protocol_handler):
    """Test sending a response."""
    # Create a mock for _send_message
    protocol_handler._send_message = AsyncMock()
    
    # Send a response
    await protocol_handler._send_response("test-id", {"result": "success"})
    
    # Check that _send_message was called with the correct data
    call_args = protocol_handler._send_message.call_args[0][0]
    assert call_args["type"] == "response"
    assert call_args["id"] == "test-id"
    assert call_args["data"] == {"result": "success"}


@pytest.mark.asyncio
async def test_send_error(protocol_handler):
    """Test sending an error."""
    # Create a mock for _send_message
    protocol_handler._send_message = AsyncMock()
    
    # Send an error
    await protocol_handler._send_error("error_code", "Error message", "test-id")
    
    # Check that _send_message was called with the correct data
    call_args = protocol_handler._send_message.call_args[0][0]
    assert call_args["type"] == "error"
    assert call_args["id"] == "test-id"
    assert call_args["error"]["code"] == "error_code"
    assert call_args["error"]["message"] == "Error message"


@pytest.mark.asyncio
async def test_send_message(protocol_handler):
    """Test sending a message."""
    # Create a mock for stdout_writer
    mock_writer = AsyncMock()
    protocol_handler._stdout_writer = mock_writer
    
    # Send a message
    message = {
        "type": "test",
        "id": "test-id",
        "data": {"key": "value"}
    }
    await protocol_handler._send_message(message)
    
    # Check that the writer was called with the correct data
    expected_bytes = (json.dumps(message) + "\n").encode("utf-8")
    mock_writer.write.assert_called_once_with(expected_bytes)
    mock_writer.drain.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_no_writer(protocol_handler):
    """Test sending a message with no writer."""
    # Ensure the writer is None
    protocol_handler._stdout_writer = None
    
    # Try to send a message
    message = {
        "type": "test",
        "id": "test-id",
        "data": {"key": "value"}
    }
    with pytest.raises(MCPConnectionError):
        await protocol_handler._send_message(message)