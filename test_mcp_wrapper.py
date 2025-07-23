#!/usr/bin/env python3
"""
Simple MCP wrapper for testing.
"""

import asyncio
import json
import logging
import os
import sys
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

class SimpleMCPWrapper:
    """Simple MCP wrapper for testing."""
    
    def __init__(self):
        """Initialize the wrapper."""
        self.running = False
        self.tools = {
            "product_info": {
                "name": "product_info",
                "description": "Generate structured product information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The product query"
                        }
                    },
                    "required": ["query"]
                }
            },
            "person_profile": {
                "name": "person_profile",
                "description": "Generate structured person profile information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The person query"
                        }
                    },
                    "required": ["query"]
                }
            },
            "api_endpoint": {
                "name": "api_endpoint",
                "description": "Generate structured API endpoint information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The API query"
                        }
                    },
                    "required": ["query"]
                }
            },
            "troubleshooting_guide": {
                "name": "troubleshooting_guide",
                "description": "Generate structured troubleshooting guide",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The troubleshooting query"
                        }
                    },
                    "required": ["query"]
                }
            },
            "article_summary": {
                "name": "article_summary",
                "description": "Generate structured article summary",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The article query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    async def start(self):
        """Start the wrapper."""
        self.running = True
        logger.info("MCP wrapper started")
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self.stop())
            )
        
        # Start the message processing loop
        await self.process_messages()
    
    async def stop(self):
        """Stop the wrapper."""
        if not self.running:
            return
        
        self.running = False
        logger.info("MCP wrapper stopped")
    
    async def process_messages(self):
        """Process incoming messages from stdin."""
        stdin_reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(stdin_reader)
        
        loop = asyncio.get_running_loop()
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        # For stdout, we need to use a different approach
        stdout_transport, _ = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, 
            os.fdopen(sys.stdout.fileno(), 'wb')
        )
        stdout_writer = asyncio.StreamWriter(stdout_transport, None, None, loop)
        
        # Buffer for incomplete data
        buffer = b""
        
        while self.running:
            try:
                # Try to read a line first to check for headers
                line = await stdin_reader.readline()
                if not line:
                    logger.info("End of input, stopping")
                    break
                
                # Add the line to the buffer
                buffer += line
                
                # Check if this is a header or a direct JSON message
                try:
                    # Try to parse as JSON
                    message = buffer.decode('utf-8')
                    request = json.loads(message)
                    logger.info(f"Received direct JSON request: {request}")
                    
                    # Process the message
                    await self.handle_jsonrpc_request(stdout_writer, request)
                    
                    # Clear the buffer
                    buffer = b""
                    continue
                except json.JSONDecodeError:
                    # Not a valid JSON, might be a header
                    pass
                
                # Try to parse as a header
                header = line.decode('utf-8').strip()
                if header.startswith("Content-Length: "):
                    # Extract the content length
                    content_length = int(header[16:])
                    
                    # Read the separator line
                    separator = await stdin_reader.readline()
                    if separator.decode('utf-8').strip() != "":
                        logger.error("Expected empty line after header")
                        buffer = b""
                        continue
                    
                    # Read the content
                    content = await stdin_reader.readexactly(content_length)
                    message = content.decode('utf-8')
                    
                    # Parse the message
                    try:
                        request = json.loads(message)
                        logger.info(f"Received request with header: {request}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
                        await self.send_error_response(stdout_writer, -32700, "Parse error", request_id=None)
                        buffer = b""
                        continue
                    
                    # Process the message
                    await self.handle_jsonrpc_request(stdout_writer, request)
                    
                    # Clear the buffer
                    buffer = b""
                else:
                    # Not a valid header, keep reading
                    logger.warning(f"Unexpected input: {header}")
                    
                    # If the buffer gets too large, clear it
                    if len(buffer) > 10000:
                        logger.error("Buffer too large, clearing")
                        buffer = b""
                
            except asyncio.IncompleteReadError:
                logger.info("End of input, stopping")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await self.send_error_response(stdout_writer, -32603, f"Internal error: {e}", request_id=None)
                buffer = b""
    
    async def handle_jsonrpc_request(self, writer, request):
        """
        Handle a JSON-RPC request.
        
        Args:
            writer: The stdout writer
            request: The request to handle
        """
        # Extract the request ID
        request_id = request.get("id")
        
        # Check if this is a valid JSON-RPC request
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            await self.send_error_response(writer, -32600, "Invalid Request: Not a valid JSON-RPC 2.0 request", request_id)
            return
        
        # Extract the method
        method = request.get("method")
        if not method:
            await self.send_error_response(writer, -32600, "Invalid Request: Method not specified", request_id)
            return
        
        # Handle different methods
        try:
            if method == "initialize":
                await self.handle_initialize(writer, request)
            elif method == "listTools":
                await self.handle_list_tools(writer, request)
            elif method == "invoke":
                await self.handle_invoke(writer, request)
            elif method == "shutdown":
                await self.handle_shutdown(writer, request)
            else:
                await self.send_error_response(writer, -32601, f"Method not found: {method}", request_id)
        except Exception as e:
            logger.error(f"Error handling method {method}: {e}")
            await self.send_error_response(writer, -32603, f"Internal error: {e}", request_id)
    
    async def handle_initialize(self, writer, request):
        """
        Handle an initialize request.
        
        Args:
            writer: The stdout writer
            request: The request to handle
        """
        request_id = request.get("id")
        
        # Return a success response
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "capabilities": {
                    "supportsToolInvocation": True
                },
                "serverInfo": {
                    "name": "fixed-schema-mcp-server",
                    "version": "0.1.0"
                }
            }
        }
        
        await self.send_jsonrpc_response(writer, response)
    
    async def handle_list_tools(self, writer, request):
        """
        Handle a listTools request.
        
        Args:
            writer: The stdout writer
            request: The request to handle
        """
        request_id = request.get("id")
        
        # Return the list of tools
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
        
        await self.send_jsonrpc_response(writer, response)
    
    async def handle_invoke(self, writer, request):
        """
        Handle an invoke request.
        
        Args:
            writer: The stdout writer
            request: The request to handle
        """
        request_id = request.get("id")
        params = request.get("params", {})
        
        # Extract the tool name and parameters
        tool_name = params.get("name")
        tool_params = params.get("parameters", {})
        
        if not tool_name:
            await self.send_error_response(writer, -32602, "Invalid params: Tool name not specified", request_id)
            return
        
        # Check if the tool exists
        if tool_name not in self.tools:
            await self.send_error_response(writer, -32602, f"Invalid params: Tool not found: {tool_name}", request_id)
            return
        
        # Generate a mock response based on the tool
        result = await self.generate_mock_response(tool_name, tool_params)
        
        # Return the result
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
        await self.send_jsonrpc_response(writer, response)
    
    async def handle_shutdown(self, writer, request):
        """
        Handle a shutdown request.
        
        Args:
            writer: The stdout writer
            request: The request to handle
        """
        request_id = request.get("id")
        
        # Return a success response
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": None
        }
        
        await self.send_jsonrpc_response(writer, response)
        
        # Stop the wrapper
        self.running = False
    
    async def generate_mock_response(self, tool_name, params):
        """
        Generate a mock response for a tool.
        
        Args:
            tool_name: The name of the tool
            params: The tool parameters
            
        Returns:
            The mock response
        """
        query = params.get("query", "")
        
        if tool_name == "product_info":
            return {
                "name": "Example Product",
                "description": f"This is an example product based on query: {query}",
                "price": 99.99,
                "category": "Electronics",
                "features": ["Feature 1", "Feature 2", "Feature 3"],
                "rating": 4.5,
                "inStock": True
            }
        elif tool_name == "person_profile":
            return {
                "name": "John Doe",
                "age": 30,
                "occupation": "Software Engineer",
                "skills": ["Python", "JavaScript", "AWS"],
                "contact": {
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567"
                }
            }
        elif tool_name == "api_endpoint":
            return {
                "path": "/api/v1/users",
                "method": "GET",
                "description": "Get a list of users",
                "parameters": [
                    {
                        "name": "page",
                        "type": "integer",
                        "required": False,
                        "description": "Page number"
                    },
                    {
                        "name": "limit",
                        "type": "integer",
                        "required": False,
                        "description": "Number of items per page"
                    }
                ],
                "responses": [
                    {
                        "code": 200,
                        "description": "Success",
                        "example": {
                            "users": [
                                {"id": 1, "name": "User 1"},
                                {"id": 2, "name": "User 2"}
                            ],
                            "total": 2
                        }
                    },
                    {
                        "code": 401,
                        "description": "Unauthorized"
                    }
                ]
            }
        elif tool_name == "troubleshooting_guide":
            return {
                "issue": f"Problem with {query}",
                "symptoms": [
                    "Symptom 1",
                    "Symptom 2",
                    "Symptom 3"
                ],
                "causes": [
                    "Cause 1",
                    "Cause 2"
                ],
                "solutions": [
                    {
                        "step": 1,
                        "description": "First step to solve the issue"
                    },
                    {
                        "step": 2,
                        "description": "Second step to solve the issue"
                    }
                ],
                "preventionTips": [
                    "Tip 1",
                    "Tip 2"
                ]
            }
        elif tool_name == "article_summary":
            return {
                "title": f"Summary of {query}",
                "author": "AI Assistant",
                "date": "2025-07-23",
                "summary": "This is a summary of the article.",
                "keyPoints": [
                    "Key point 1",
                    "Key point 2",
                    "Key point 3"
                ],
                "conclusion": "This is the conclusion of the article."
            }
        else:
            return {
                "message": f"Generated response for tool: {tool_name}",
                "query": query
            }
    
    async def send_jsonrpc_response(self, writer, response):
        """
        Send a JSON-RPC response to stdout.
        
        Args:
            writer: The stdout writer
            response: The response to send
        """
        try:
            # Convert the response to JSON
            response_json = json.dumps(response)
            logger.info(f"Sending response: {response_json}")
            
            # Encode the response
            content = response_json.encode('utf-8')
            
            # Create the header
            header = f"Content-Length: {len(content)}\r\n\r\n".encode('utf-8')
            
            # Write the header and content
            writer.write(header)
            writer.write(content)
            await writer.drain()
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    async def send_error_response(self, writer, code, message, request_id):
        """
        Send a JSON-RPC error response to stdout.
        
        Args:
            writer: The stdout writer
            code: The error code
            message: The error message
            request_id: The request ID
        """
        try:
            # Create the error response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": code,
                    "message": message
                }
            }
            
            # Send the response
            await self.send_jsonrpc_response(writer, response)
            
        except Exception as e:
            logger.error(f"Error sending error response: {e}")

async def main():
    """Run the MCP wrapper."""
    # Create and start the wrapper
    wrapper = SimpleMCPWrapper()
    await wrapper.start()

if __name__ == "__main__":
    asyncio.run(main())