"""
MCP protocol handling for the Fixed Schema Response MCP Server.

This module provides functionality for handling the Model Context Protocol (MCP)
communication between the server and clients.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any, Optional, Callable, Awaitable, List, Union

from fixed_schema_mcp_server.core.exceptions import MCPProtocolError, MCPConnectionError

logger = logging.getLogger(__name__)

class MCPProtocolHandler:
    """
    Handler for the Model Context Protocol (MCP).
    
    This class is responsible for handling the MCP communication between
    the server and clients, including message parsing, validation, and routing.
    """
    
    def __init__(self):
        """Initialize the protocol handler."""
        self._request_handlers = {}
        self._initialized = False
        self._running = False
        self._stdin_reader = None
        self._stdout_writer = None
    
    async def initialize(self) -> None:
        """
        Initialize the protocol handler.
        
        Raises:
            MCPConnectionError: If there is an error initializing the handler
        """
        try:
            # Set up stdin/stdout for communication
            loop = asyncio.get_running_loop()
            
            if sys.platform == 'win32':
                # Windows-specific setup
                self._stdin_reader = asyncio.StreamReader()
                protocol = asyncio.StreamReaderProtocol(self._stdin_reader)
                await loop.connect_read_pipe(lambda: protocol, sys.stdin)
                
                self._stdout_writer = asyncio.StreamWriter(sys.stdout.buffer, protocol, None, loop)
            else:
                # Unix-like setup
                reader = asyncio.StreamReader()
                protocol = asyncio.StreamReaderProtocol(reader)
                await loop.connect_read_pipe(lambda: protocol, sys.stdin)
                self._stdin_reader = reader
                
                transport, _ = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, os.fdopen(sys.stdout.fileno(), 'wb'))
                self._stdout_writer = asyncio.StreamWriter(transport, None, None, loop)
            
            self._initialized = True
            logger.info("MCP protocol handler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP protocol handler: {e}")
            raise MCPConnectionError(f"Failed to initialize protocol handler: {e}")
    
    async def start(self) -> None:
        """
        Start the protocol handler and begin processing messages.
        
        Raises:
            MCPConnectionError: If there is an error starting the handler
        """
        if not self._initialized:
            raise MCPConnectionError("Protocol handler not initialized")
        
        if self._running:
            logger.warning("Protocol handler is already running")
            return
        
        try:
            self._running = True
            logger.info("MCP protocol handler started")
            
            # Start the message processing loop
            asyncio.create_task(self._process_messages())
            
        except Exception as e:
            self._running = False
            logger.error(f"Failed to start MCP protocol handler: {e}")
            raise MCPConnectionError(f"Failed to start protocol handler: {e}")
    
    async def stop(self) -> None:
        """
        Stop the protocol handler.
        
        Raises:
            MCPConnectionError: If there is an error stopping the handler
        """
        if not self._running:
            logger.warning("Protocol handler is not running")
            return
        
        try:
            self._running = False
            logger.info("MCP protocol handler stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop MCP protocol handler: {e}")
            raise MCPConnectionError(f"Failed to stop protocol handler: {e}")
    
    def register_request_handler(self, request_type: str, handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]) -> None:
        """
        Register a handler for a specific request type.
        
        Args:
            request_type: The type of request to handle
            handler: The handler function to call for this request type
        """
        self._request_handlers[request_type] = handler
        logger.debug(f"Registered handler for request type: {request_type}")
    
    async def _process_messages(self) -> None:
        """
        Process incoming messages from stdin.
        
        This method runs in a loop, reading messages from stdin,
        parsing them, and routing them to the appropriate handler.
        """
        while self._running:
            try:
                # Read a message from stdin
                message = await self._read_message()
                
                if message is None:
                    # End of input, exit the loop
                    logger.info("End of input, stopping message processing")
                    self._running = False
                    break
                
                # Parse the message
                try:
                    parsed_message = json.loads(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                    await self._send_error_response("invalid_json", f"Failed to parse message: {e}")
                    continue
                
                # Process the message
                await self._handle_message(parsed_message)
                
            except asyncio.CancelledError:
                # Task was cancelled, exit the loop
                logger.info("Message processing task cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await self._send_error_response("internal_error", f"Error processing message: {e}")
    
    async def _read_message(self) -> Optional[str]:
        """
        Read a message from stdin.
        
        Returns:
            The message as a string, or None if the input is closed
            
        Raises:
            MCPProtocolError: If there is an error reading the message
        """
        try:
            # Read the header line
            header_line = await self._stdin_reader.readline()
            
            if not header_line:
                # End of input
                return None
            
            # Parse the header
            header = header_line.decode('utf-8').strip()
            
            if not header.startswith("Content-Length: "):
                raise MCPProtocolError(f"Invalid header: {header}")
            
            # Extract the content length
            content_length = int(header[16:])
            
            # Read the separator line
            separator = await self._stdin_reader.readline()
            
            if separator.decode('utf-8').strip() != "":
                raise MCPProtocolError("Expected empty line after header")
            
            # Read the content
            content = await self._stdin_reader.readexactly(content_length)
            
            return content.decode('utf-8')
            
        except asyncio.IncompleteReadError:
            # End of input
            return None
        except Exception as e:
            logger.error(f"Error reading message: {e}")
            raise MCPProtocolError(f"Error reading message: {e}")
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a parsed message.
        
        Args:
            message: The parsed message as a dictionary
            
        Raises:
            MCPProtocolError: If there is an error handling the message
        """
        try:
            # Extract the request type
            request_type = message.get("type")
            
            if not request_type:
                raise MCPProtocolError("Message missing 'type' field")
            
            # Get the handler for this request type
            handler = self._request_handlers.get(request_type)
            
            if not handler:
                logger.warning(f"No handler registered for request type: {request_type}")
                await self._send_error_response("unknown_request_type", f"Unknown request type: {request_type}")
                return
            
            # Call the handler
            response = await handler(message)
            
            # Send the response
            await self._send_response(response)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error_response("internal_error", f"Error handling message: {e}")
    
    async def _send_response(self, response: Dict[str, Any]) -> None:
        """
        Send a response to stdout.
        
        Args:
            response: The response to send
            
        Raises:
            MCPProtocolError: If there is an error sending the response
        """
        try:
            # Convert the response to JSON
            response_json = json.dumps(response)
            
            # Send the response
            await self._write_message(response_json)
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            raise MCPProtocolError(f"Error sending response: {e}")
    
    async def _send_error_response(self, error_code: str, error_message: str) -> None:
        """
        Send an error response to stdout.
        
        Args:
            error_code: The error code
            error_message: The error message
            
        Raises:
            MCPProtocolError: If there is an error sending the response
        """
        try:
            # Create the error response
            response = {
                "status": "error",
                "error": {
                    "code": error_code,
                    "message": error_message
                }
            }
            
            # Send the response
            await self._send_response(response)
            
        except Exception as e:
            logger.error(f"Error sending error response: {e}")
            raise MCPProtocolError(f"Error sending error response: {e}")
    
    async def _write_message(self, message: str) -> None:
        """
        Write a message to stdout.
        
        Args:
            message: The message to write
            
        Raises:
            MCPProtocolError: If there is an error writing the message
        """
        try:
            # Encode the message
            content = message.encode('utf-8')
            
            # Create the header
            header = f"Content-Length: {len(content)}\r\n\r\n".encode('utf-8')
            
            # Write the header and content
            self._stdout_writer.write(header)
            self._stdout_writer.write(content)
            await self._stdout_writer.drain()
            
        except Exception as e:
            logger.error(f"Error writing message: {e}")
            raise MCPProtocolError(f"Error writing message: {e}")