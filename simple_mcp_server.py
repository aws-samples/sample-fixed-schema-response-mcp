#!/usr/bin/env python3
"""
Very simple MCP server.
"""

import json
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the MCP server."""
    logger.info("MCP server started")
    
    # Define the tools
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
    
    # Process messages
    running = True
    while running:
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
                    # Extract the protocol version from the request
                    protocol_version = params.get("protocolVersion", "2025-03-26")
                    
                    # Send the response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": protocol_version,
                            "capabilities": {
                                "supportsToolInvocation": True
                            },
                            "serverInfo": {
                                "name": "fixed-schema-mcp-server",
                                "version": "0.1.0"
                            }
                        }
                    }
                    logger.info(f"Sending response: {response}")
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                    
                    # Send a listTools response
                    list_tools_response = {
                        "jsonrpc": "2.0",
                        "id": 1001,
                        "result": {
                            "tools": tools
                        }
                    }
                    logger.info(f"Sending listTools response: {list_tools_response}")
                    sys.stdout.write(json.dumps(list_tools_response) + "\n")
                    sys.stdout.flush()
                elif method == "listTools":
                    logger.info("Received listTools request")
                    
                    # Send the response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": tools
                        }
                    }
                    logger.info(f"Sending listTools response: {response}")
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                elif method == "invoke":
                    # Extract the tool name and parameters
                    tool_name = params.get("name")
                    tool_params = params.get("parameters", {})
                    query = tool_params.get("query", "")
                    
                    # Generate a mock response based on the tool
                    if tool_name == "product_info":
                        result = {
                            "name": f"Example Product for {query}",
                            "description": f"This is an example product based on query: {query}",
                            "price": 99.99,
                            "category": "Electronics",
                            "features": ["Feature 1", "Feature 2", "Feature 3"],
                            "rating": 4.5,
                            "inStock": True
                        }
                    elif tool_name == "person_profile":
                        result = {
                            "name": f"{query}",
                            "age": 30,
                            "occupation": "Software Engineer",
                            "skills": ["Python", "JavaScript", "AWS"],
                            "contact": {
                                "email": f"{query.lower().replace(' ', '.')}@example.com",
                                "phone": "555-123-4567"
                            }
                        }
                    elif tool_name == "api_endpoint":
                        result = {
                            "path": f"/api/v1/{query.lower().replace(' ', '-')}",
                            "method": "GET",
                            "description": f"Get information about {query}",
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
                                        "data": [
                                            {"id": 1, "name": "Item 1"},
                                            {"id": 2, "name": "Item 2"}
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
                        result = {
                            "issue": f"Problem with {query}",
                            "symptoms": [
                                f"{query} is not working properly",
                                "Error messages appear",
                                "System performance is degraded"
                            ],
                            "causes": [
                                "Configuration issues",
                                "Software bugs"
                            ],
                            "solutions": [
                                {
                                    "step": 1,
                                    "description": f"Check if {query} is properly configured"
                                },
                                {
                                    "step": 2,
                                    "description": "Restart the system"
                                },
                                {
                                    "step": 3,
                                    "description": "Contact support if the issue persists"
                                }
                            ],
                            "preventionTips": [
                                "Regularly update your software",
                                "Follow best practices"
                            ]
                        }
                    elif tool_name == "article_summary":
                        result = {
                            "title": f"Summary of {query}",
                            "author": "AI Assistant",
                            "date": "2025-07-23",
                            "summary": f"This is a summary of an article about {query}.",
                            "keyPoints": [
                                f"{query} is an important topic",
                                "There are many aspects to consider",
                                "Further research is needed"
                            ],
                            "conclusion": f"In conclusion, {query} is a fascinating subject that deserves attention."
                        }
                    else:
                        result = {
                            "message": f"Generated response for tool: {tool_name}",
                            "query": query
                        }
                    
                    # Send the response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                    logger.info(f"Sending response: {response}")
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                elif method == "shutdown":
                    # Send the response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": None
                    }
                    logger.info(f"Sending response: {response}")
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                    
                    # Stop the server
                    running = False
                elif method == "notifications/initialized":
                    # This is a notification, no response needed
                    logger.info("Received notifications/initialized notification")
                else:
                    # Method not found
                    if request_id is not None:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            }
                        }
                        logger.info(f"Sending response: {response}")
                        sys.stdout.write(json.dumps(response) + "\n")
                        sys.stdout.flush()
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {line}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    logger.info("MCP server stopped")

if __name__ == "__main__":
    main()