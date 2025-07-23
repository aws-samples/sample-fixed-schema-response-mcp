#!/usr/bin/env python3
"""
MCP wrapper for the Fixed Schema Response MCP Server.

This script provides a wrapper that implements the MCP protocol
and forwards requests to the HTTP server.
"""

import json
import sys
import logging
import os
import argparse
import requests
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

class MCPWrapper:
    """MCP wrapper for the Fixed Schema Response MCP Server."""
    
    def __init__(self, http_host="localhost", http_port=8081):
        """
        Initialize the wrapper.
        
        Args:
            http_host: The HTTP server host
            http_port: The HTTP server port
        """
        self.http_host = http_host
        self.http_port = http_port
        self.http_base_url = f"http://{http_host}:{http_port}"
        self.running = False
        self.tools = {}
        
        # Try to load the tools from the HTTP server
        try:
            response = requests.get(f"{self.http_base_url}/schemas")
            if response.status_code == 200:
                schemas = response.json().get("schemas", [])
                for schema_name in schemas:
                    self.tools[schema_name] = {
                        "name": schema_name,
                        "description": f"Generate structured {schema_name} information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": f"The {schema_name} query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
        except Exception as e:
            logger.error(f"Failed to load tools from HTTP server: {e}")
            # Use default tools
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
    
    def start(self):
        """Start the wrapper."""
        self.running = True
        logger.info("MCP wrapper started")
        
        # Process messages
        while self.running:
            try:
                # Read a line
                line = sys.stdin.readline()
                if not line:
                    logger.info("End of input, stopping")
                    break
                
                # Try to parse as JSON
                try:
                    request = json.loads(line)
                    logger.info(f"Received request: {request}")
                    
                    # Extract the method and params
                    method = request.get("method")
                    params = request.get("params", {})
                    request_id = request.get("id")
                    
                    # Handle the method
                    if method == "initialize":
                        logger.info(f"Handling initialize request: {params}")
                        result = self.handle_initialize(params)
                        logger.info(f"Initialize result: {result}")
                    elif method == "listTools":
                        logger.info(f"Handling listTools request: {params}")
                        result = self.handle_list_tools(params)
                        logger.info(f"ListTools result: {result}")
                    elif method == "invoke":
                        logger.info(f"Handling invoke request: {params}")
                        result = self.handle_invoke(params)
                        logger.info(f"Invoke result: {result}")
                    elif method == "shutdown":
                        logger.info(f"Handling shutdown request: {params}")
                        result = self.handle_shutdown(params)
                        logger.info(f"Shutdown result: {result}")
                        self.running = False
                    else:
                        # Method not found
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            }
                        }
                        sys.stdout.write(json.dumps(response) + "\n")
                        sys.stdout.flush()
                        continue
                    
                    # Send the response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                    logger.info(f"Sending response: {response}")
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {line}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        
        logger.info("MCP wrapper stopped")
    
    def handle_initialize(self, params):
        """
        Handle an initialize request.
        
        Args:
            params: The request parameters
            
        Returns:
            The response result
        """
        # Extract the protocol version from the request
        protocol_version = params.get("protocolVersion", "2025-03-26")
        
        return {
            "protocolVersion": protocol_version,
            "capabilities": {
                "supportsToolInvocation": True
            },
            "serverInfo": {
                "name": "fixed-schema-mcp-server",
                "version": "0.1.0"
            }
        }
    
    def handle_list_tools(self, params):
        """
        Handle a listTools request.
        
        Args:
            params: The request parameters
            
        Returns:
            The response result
        """
        # Define the tools directly
        tools = [
            {
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
            {
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
            {
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
            {
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
            {
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
        ]
        
        # Store the tools for later use
        self.tools = {tool["name"]: tool for tool in tools}
        
        logger.info(f"Returning tools: {tools}")
        return {
            "tools": tools
        }
    
    def handle_invoke(self, params):
        """
        Handle an invoke request.
        
        Args:
            params: The request parameters
            
        Returns:
            The response result
        """
        tool_name = params.get("name")
        tool_params = params.get("parameters", {})
        query = tool_params.get("query", "")
        
        # Check if the tool exists
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Forward the request to the HTTP server
        try:
            response = requests.post(
                f"{self.http_base_url}/query",
                json={
                    "query": query,
                    "schema": tool_name,
                    "parameters": {}
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"HTTP server returned status {response.status_code}")
            
            result = response.json()
            
            # Check if the result is an error
            if result.get("status") == "error":
                raise ValueError(result.get("error", {}).get("message", "Unknown error"))
            
            # Return the result
            return result.get("data", {})
            
        except requests.RequestException as e:
            logger.error(f"HTTP request error: {e}")
            raise ValueError(f"HTTP request error: {e}")
    
    def handle_shutdown(self, params):
        """
        Handle a shutdown request.
        
        Args:
            params: The request parameters
            
        Returns:
            The response result
        """
        return None

def main():
    """Run the MCP wrapper."""
    parser = argparse.ArgumentParser(description="MCP wrapper for the Fixed Schema Response MCP Server")
    parser.add_argument("--host", type=str, default="localhost", help="HTTP server host")
    parser.add_argument("--port", type=int, default=8081, help="HTTP server port")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(args.log_level.upper())
    
    # Create and start the wrapper
    wrapper = MCPWrapper(http_host=args.host, http_port=args.port)
    wrapper.start()

if __name__ == "__main__":
    main()