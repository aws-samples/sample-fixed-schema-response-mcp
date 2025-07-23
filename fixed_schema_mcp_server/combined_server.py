#!/usr/bin/env python3
"""
Combined HTTP and MCP server for the Fixed Schema Response MCP Server.
"""

import json
import sys
import logging
import argparse
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

# Define the tools and schemas
SCHEMAS = {
    "product_info": {
        "name": "product_info",
        "description": "Schema for product information",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "price": {"type": "number"},
                "category": {"type": "string"},
                "features": {"type": "array", "items": {"type": "string"}},
                "rating": {"type": "number"},
                "inStock": {"type": "boolean"}
            },
            "required": ["name", "price", "category"]
        }
    },
    "person_profile": {
        "name": "person_profile",
        "description": "Schema for person profile information",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "occupation": {"type": "string"},
                "skills": {"type": "array", "items": {"type": "string"}},
                "contact": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "phone": {"type": "string"}
                    }
                }
            },
            "required": ["name"]
        }
    },
    "api_endpoint": {
        "name": "api_endpoint",
        "description": "Schema for API endpoint information",
        "schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "method": {"type": "string"},
                "description": {"type": "string"},
                "parameters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "required": {"type": "boolean"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "responses": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer"},
                            "description": {"type": "string"},
                            "example": {"type": "object"}
                        }
                    }
                }
            },
            "required": ["path", "method"]
        }
    },
    "troubleshooting_guide": {
        "name": "troubleshooting_guide",
        "description": "Schema for troubleshooting guide",
        "schema": {
            "type": "object",
            "properties": {
                "issue": {"type": "string"},
                "symptoms": {"type": "array", "items": {"type": "string"}},
                "causes": {"type": "array", "items": {"type": "string"}},
                "solutions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step": {"type": "integer"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "preventionTips": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["issue", "solutions"]
        }
    },
    "article_summary": {
        "name": "article_summary",
        "description": "Schema for article summary",
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string"},
                "date": {"type": "string"},
                "summary": {"type": "string"},
                "keyPoints": {"type": "array", "items": {"type": "string"}},
                "conclusion": {"type": "string"}
            },
            "required": ["title", "summary"]
        }
    }
}

TOOLS = [
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

class HTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Fixed Schema Response MCP Server."""
    
    def _set_headers(self, status_code=200, content_type="application/json"):
        """Set the response headers."""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests."""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == "/health":
            # Health check
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "health": {
                    "server": {
                        "status": "healthy",
                        "uptime": 0
                    },
                    "model": {
                        "status": "healthy",
                        "name": "mock-model"
                    }
                }
            }).encode())
        elif path == "/schemas":
            # List schemas
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "schemas": list(SCHEMAS.keys())
            }).encode())
        elif path.startswith("/schema/"):
            # Get schema
            schema_name = path.split("/")[-1]
            if schema_name in SCHEMAS:
                self._set_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "schema": SCHEMAS[schema_name]
                }).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({
                    "status": "error",
                    "error": {
                        "code": "schema_not_found",
                        "message": f"Schema not found: {schema_name}"
                    }
                }).encode())
        else:
            # Not found
            self._set_headers(404)
            self.wfile.write(json.dumps({
                "status": "error",
                "error": {
                    "code": "not_found",
                    "message": f"Path not found: {path}"
                }
            }).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")
        
        try:
            request = json.loads(post_data)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({
                "status": "error",
                "error": {
                    "code": "invalid_json",
                    "message": "Invalid JSON in request body"
                }
            }).encode())
            return
        
        if self.path == "/query":
            # Process query
            query = request.get("query")
            schema_name = request.get("schema")
            
            if not query:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "status": "error",
                    "error": {
                        "code": "missing_query",
                        "message": "Query is required"
                    }
                }).encode())
                return
            
            if not schema_name:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "status": "error",
                    "error": {
                        "code": "missing_schema",
                        "message": "Schema is required"
                    }
                }).encode())
                return
            
            if schema_name not in SCHEMAS:
                self._set_headers(404)
                self.wfile.write(json.dumps({
                    "status": "error",
                    "error": {
                        "code": "schema_not_found",
                        "message": f"Schema not found: {schema_name}"
                    }
                }).encode())
                return
            
            # Generate a response based on the schema
            if schema_name == "product_info":
                data = {
                    "name": f"Example Product for {query}",
                    "description": f"This is an example product based on query: {query}",
                    "price": 99.99,
                    "category": "Electronics",
                    "features": ["Feature 1", "Feature 2", "Feature 3"],
                    "rating": 4.5,
                    "inStock": True
                }
            elif schema_name == "person_profile":
                data = {
                    "name": f"{query}",
                    "age": 30,
                    "occupation": "Software Engineer",
                    "skills": ["Python", "JavaScript", "AWS"],
                    "contact": {
                        "email": f"{query.lower().replace(' ', '.')}@example.com",
                        "phone": "555-123-4567"
                    }
                }
            elif schema_name == "api_endpoint":
                data = {
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
            elif schema_name == "troubleshooting_guide":
                data = {
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
            elif schema_name == "article_summary":
                data = {
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
                data = {
                    "message": f"Generated response for schema: {schema_name}",
                    "query": query
                }
            
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "data": data,
                "metadata": {
                    "model": "mock-model",
                    "processing_time": 0.1
                }
            }).encode())
        else:
            # Not found
            self._set_headers(404)
            self.wfile.write(json.dumps({
                "status": "error",
                "error": {
                    "code": "not_found",
                    "message": f"Path not found: {self.path}"
                }
            }).encode())

def initialize(params):
    """Handle an initialize request."""
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

def list_tools(params):
    """Handle a listTools request."""
    return {
        "tools": TOOLS
    }

def invoke(params):
    """Handle an invoke request."""
    tool_name = params.get("name")
    tool_params = params.get("parameters", {})
    query = tool_params.get("query", "")
    
    # Generate a mock response based on the tool
    if tool_name == "product_info":
        return {
            "name": f"Example Product for {query}",
            "description": f"This is an example product based on query: {query}",
            "price": 99.99,
            "category": "Electronics",
            "features": ["Feature 1", "Feature 2", "Feature 3"],
            "rating": 4.5,
            "inStock": True
        }
    elif tool_name == "person_profile":
        return {
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
        return {
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
        return {
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
        return {
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
        return {
            "message": f"Generated response for tool: {tool_name}",
            "query": query
        }

def shutdown(params):
    """Handle a shutdown request."""
    return None

def process_mcp_messages():
    """Process MCP messages from stdin."""
    logger.info("MCP server started")
    
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
                    result = initialize(params)
                elif method == "listTools":
                    result = list_tools(params)
                elif method == "invoke":
                    result = invoke(params)
                elif method == "shutdown":
                    result = shutdown(params)
                    running = False
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
    
    logger.info("MCP server stopped")

def main():
    """Run the combined server."""
    parser = argparse.ArgumentParser(description="Combined HTTP and MCP server for the Fixed Schema Response MCP Server")
    parser.add_argument("--host", type=str, default="localhost", help="HTTP server host")
    parser.add_argument("--port", type=int, default=8081, help="HTTP server port")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    parser.add_argument("--http-only", action="store_true", help="Run only the HTTP server")
    parser.add_argument("--mcp-only", action="store_true", help="Run only the MCP server")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(args.log_level.upper())
    
    # Run the appropriate server(s)
    if args.mcp_only:
        # Run only the MCP server
        process_mcp_messages()
    elif args.http_only:
        # Run only the HTTP server
        server_address = (args.host, args.port)
        httpd = HTTPServer(server_address, HTTPRequestHandler)
        logger.info(f"HTTP server started on {args.host}:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down")
            httpd.server_close()
    else:
        # Run both servers
        # This is not possible in a single process, so we'll run the MCP server
        process_mcp_messages()

if __name__ == "__main__":
    main()