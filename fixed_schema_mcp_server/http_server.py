#!/usr/bin/env python3
"""
Simple HTTP server that implements the MCP protocol.
"""

import json
import logging
import os
import sys
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Mock responses for different schemas
MOCK_RESPONSES = {
    "product_info": {
        "name": "iPhone 15 Pro",
        "description": "The latest flagship smartphone from Apple featuring a powerful A17 Pro chip, a stunning Super Retina XDR display, and an advanced camera system.",
        "price": 999.99,
        "category": "Smartphones",
        "features": [
            "A17 Pro chip",
            "48MP main camera",
            "Titanium design",
            "Action button",
            "USB-C connector"
        ]
    },
    "article_summary": {
        "title": "Recent Breakthroughs in Artificial Intelligence",
        "summary": "AI continues to advance rapidly across multiple domains, with notable progress in language models, computer vision, and robotics.",
        "key_points": [
            "GPT-4 demonstrates improved reasoning and task performance compared to previous models",
            "AI image generation tools like DALL-E 3 and Midjourney show significant enhancements in quality and control",
            "Researchers develop more energy-efficient AI models to reduce environmental impact",
            "Advancements in AI-powered robotics lead to more dexterous and adaptable machines",
            "Ethical concerns and calls for responsible AI development gain prominence"
        ],
        "sentiment": "positive"
    },
    "person_profile": {
        "name": "Ada Lovelace",
        "bio": "Ada Lovelace (1815-1852) was an English mathematician and writer, known for her work on Charles Babbage's early mechanical general-purpose computer, the Analytical Engine.",
        "expertise": [
            "Mathematics",
            "Computer Science",
            "Algorithm Development"
        ],
        "achievements": [
            "Wrote the first algorithm intended to be processed by a machine",
            "Recognized the potential of computers beyond mere calculation",
            "Published detailed notes on the Analytical Engine"
        ],
        "education": [
            {
                "degree": "Private tutoring",
                "institution": "Home education",
                "year": 1835
            }
        ],
        "career": [
            {
                "position": "Collaborator",
                "organization": "Charles Babbage's Analytical Engine project",
                "period": "1842-1843"
            }
        ],
        "impact": "Ada Lovelace's work on the Analytical Engine laid the foundation for computer programming."
    },
    "api_endpoint": {
        "endpoint": "/api/users",
        "method": "POST",
        "description": "Create a new user account",
        "parameters": [
            {
                "name": "username",
                "type": "string",
                "required": True,
                "description": "Unique username for the new user",
                "location": "body"
            },
            {
                "name": "email",
                "type": "string",
                "required": True,
                "description": "Email address of the new user",
                "location": "body"
            },
            {
                "name": "password",
                "type": "string",
                "required": True,
                "description": "Password for the new user account",
                "location": "body"
            }
        ],
        "request_body": {
            "content_type": "application/json",
            "schema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string"
                    },
                    "password": {
                        "type": "string"
                    }
                },
                "required": [
                    "username",
                    "email",
                    "password"
                ]
            }
        },
        "responses": {
            "200": {
                "description": "User created successfully",
                "schema": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer"
                        },
                        "username": {
                            "type": "string"
                        },
                        "email": {
                            "type": "string"
                        }
                    }
                }
            },
            "400": {
                "description": "Invalid request body or parameters"
            }
        },
        "authentication": "None required for this endpoint",
        "example": {
            "request": "POST /api/users\nContent-Type: application/json\n\n{\n  \"username\": \"johndoe\",\n  \"email\": \"john@example.com\",\n  \"password\": \"securepassword123\"\n}",
            "response": "HTTP/1.1 200 OK\nContent-Type: application/json\n\n{\n  \"id\": 1,\n  \"username\": \"johndoe\",\n  \"email\": \"john@example.com\"\n}"
        }
    },
    "troubleshooting_guide": {
        "issue": "Docker container not starting",
        "summary": "Docker containers fail to start, preventing applications from running and causing service disruptions.",
        "symptoms": [
            "Container exits immediately after starting",
            "Error messages in Docker logs",
            "'docker ps' shows no running containers",
            "'docker start' command fails"
        ],
        "affected_systems": [
            "Docker engine",
            "Container runtime",
            "Host system",
            "Application services running in containers"
        ],
        "root_causes": [
            {
                "cause": "Incorrect container configuration",
                "likelihood": "high"
            },
            {
                "cause": "Resource constraints on the host system",
                "likelihood": "medium"
            }
        ],
        "solutions": [
            {
                "title": "Check Docker logs for error messages",
                "steps": [
                    "Run 'docker logs <container_name>' to view container logs",
                    "Analyze the output for specific error messages",
                    "Address any identified issues based on the error messages"
                ],
                "complexity": "simple",
                "prerequisites": [
                    "Docker CLI access"
                ]
            },
            {
                "title": "Verify container configuration",
                "steps": [
                    "Review the Dockerfile and docker-compose.yml (if applicable)",
                    "Ensure all required environment variables are set",
                    "Check for correct volume mounts and port mappings",
                    "Validate the container's command or entrypoint"
                ],
                "complexity": "moderate",
                "prerequisites": [
                    "Access to container configuration files"
                ]
            }
        ],
        "prevention": [
            "Regularly update Docker and container images",
            "Implement proper resource monitoring and alerting",
            "Use Docker Compose for consistent container configurations"
        ],
        "references": [
            {
                "title": "Docker troubleshooting guide",
                "url": "https://docs.docker.com/engine/troubleshoot/"
            },
            {
                "title": "Common Docker errors and solutions",
                "url": "https://www.docker.com/blog/common-docker-errors-and-solutions/"
            }
        ]
    }
}

class MCPRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        if self.path == "/health":
            self._set_headers()
            response = {"status": "healthy"}
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/schemas":
            self._set_headers()
            response = {
                "schemas": list(MOCK_RESPONSES.keys())
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        if self.path == "/query":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request = json.loads(post_data.decode())
                query = request.get("query", "")
                schema = request.get("schema", "product_info")
                
                logger.info(f"Received query: {query}, schema: {schema}")
                
                if schema in MOCK_RESPONSES:
                    response = {
                        "status": "success",
                        "data": MOCK_RESPONSES[schema],
                        "metadata": {
                            "model": "mock-model",
                            "processing_time": 0.5
                        }
                    }
                else:
                    response = {
                        "status": "error",
                        "error": {
                            "code": "schema_not_found",
                            "message": f"Schema not found: {schema}"
                        }
                    }
                
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

def run_server(host="localhost", port=8080):
    server_address = (host, port)
    httpd = HTTPServer(server_address, MCPRequestHandler)
    logger.info(f"Starting server on {host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the MCP HTTP server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    print(f"Starting server on {args.host}:{args.port}")
    run_server(args.host, args.port)