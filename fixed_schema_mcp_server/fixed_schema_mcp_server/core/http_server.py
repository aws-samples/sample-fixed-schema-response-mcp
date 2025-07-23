"""
HTTP server implementation for the Fixed Schema Response MCP Server.

This module provides an HTTP server implementation for the MCP server.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable

from aiohttp import web

from fixed_schema_mcp_server.core.exceptions import MCPServerError

logger = logging.getLogger(__name__)

class HTTPServer:
    """
    HTTP server for the Fixed Schema Response MCP Server.
    
    This class provides an HTTP server implementation for the MCP server.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        request_handler: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
    ):
        """
        Initialize the HTTP server.
        
        Args:
            host: The host to bind to
            port: The port to listen on
            request_handler: The handler for incoming requests
        """
        self._host = host
        self._port = port
        self._request_handler = request_handler
        self._app = web.Application()
        self._runner = None
        self._site = None
        self._running = False
        
        # Set up routes
        self._app.router.add_post("/query", self._handle_query)
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_get("/schemas", self._handle_get_schemas)
        self._app.router.add_get("/schema/{name}", self._handle_get_schema)
    
    async def start(self) -> None:
        """
        Start the HTTP server.
        
        Raises:
            MCPServerError: If there is an error starting the server
        """
        if self._running:
            logger.warning("HTTP server is already running")
            return
        
        try:
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()
            self._site = web.TCPSite(self._runner, self._host, self._port)
            await self._site.start()
            self._running = True
            logger.info(f"HTTP server started on {self._host}:{self._port}")
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            raise MCPServerError(f"Failed to start HTTP server: {e}")
    
    async def stop(self) -> None:
        """
        Stop the HTTP server.
        
        Raises:
            MCPServerError: If there is an error stopping the server
        """
        if not self._running:
            logger.warning("HTTP server is not running")
            return
        
        try:
            if self._site:
                await self._site.stop()
            if self._runner:
                await self._runner.cleanup()
            self._running = False
            logger.info("HTTP server stopped")
        except Exception as e:
            logger.error(f"Failed to stop HTTP server: {e}")
            raise MCPServerError(f"Failed to stop HTTP server: {e}")
    
    def set_request_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]) -> None:
        """
        Set the request handler.
        
        Args:
            handler: The handler for incoming requests
        """
        self._request_handler = handler
    
    async def _handle_query(self, request: web.Request) -> web.Response:
        """
        Handle a query request.
        
        Args:
            request: The HTTP request
            
        Returns:
            The HTTP response
        """
        try:
            # Parse the request body
            body = await request.json()
            
            # Check if we have a request handler
            if not self._request_handler:
                return web.json_response(
                    {
                        "status": "error",
                        "error": {
                            "code": "no_handler",
                            "message": "No request handler configured"
                        }
                    },
                    status=500
                )
            
            # Create the request object
            mcp_request = {
                "request_type": "generate_response",
                "query": body.get("query"),
                "schema": body.get("schema"),
                "parameters": body.get("parameters", {})
            }
            
            # Call the request handler
            response = await self._request_handler(mcp_request)
            
            # Return the response
            return web.json_response(response)
            
        except json.JSONDecodeError:
            return web.json_response(
                {
                    "status": "error",
                    "error": {
                        "code": "invalid_json",
                        "message": "Invalid JSON in request body"
                    }
                },
                status=400
            )
        except Exception as e:
            logger.error(f"Error handling query request: {e}")
            return web.json_response(
                {
                    "status": "error",
                    "error": {
                        "code": "internal_error",
                        "message": f"Internal error: {str(e)}"
                    }
                },
                status=500
            )
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """
        Handle a health check request.
        
        Args:
            request: The HTTP request
            
        Returns:
            The HTTP response
        """
        try:
            # Check if we have a request handler
            if not self._request_handler:
                return web.json_response(
                    {
                        "status": "error",
                        "error": {
                            "code": "no_handler",
                            "message": "No request handler configured"
                        }
                    },
                    status=500
                )
            
            # Create the request object
            mcp_request = {
                "request_type": "health"
            }
            
            # Call the request handler
            response = await self._request_handler(mcp_request)
            
            # Return the response
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling health request: {e}")
            return web.json_response(
                {
                    "status": "error",
                    "error": {
                        "code": "internal_error",
                        "message": f"Internal error: {str(e)}"
                    }
                },
                status=500
            )
    
    async def _handle_get_schemas(self, request: web.Request) -> web.Response:
        """
        Handle a get schemas request.
        
        Args:
            request: The HTTP request
            
        Returns:
            The HTTP response
        """
        try:
            # Check if we have a request handler
            if not self._request_handler:
                return web.json_response(
                    {
                        "status": "error",
                        "error": {
                            "code": "no_handler",
                            "message": "No request handler configured"
                        }
                    },
                    status=500
                )
            
            # Create the request object
            mcp_request = {
                "request_type": "get_schemas"
            }
            
            # Call the request handler
            response = await self._request_handler(mcp_request)
            
            # Return the response
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling get schemas request: {e}")
            return web.json_response(
                {
                    "status": "error",
                    "error": {
                        "code": "internal_error",
                        "message": f"Internal error: {str(e)}"
                    }
                },
                status=500
            )
    
    async def _handle_get_schema(self, request: web.Request) -> web.Response:
        """
        Handle a get schema request.
        
        Args:
            request: The HTTP request
            
        Returns:
            The HTTP response
        """
        try:
            # Get the schema name from the URL
            schema_name = request.match_info.get("name")
            
            # Check if we have a request handler
            if not self._request_handler:
                return web.json_response(
                    {
                        "status": "error",
                        "error": {
                            "code": "no_handler",
                            "message": "No request handler configured"
                        }
                    },
                    status=500
                )
            
            # Create the request object
            mcp_request = {
                "request_type": "get_schema",
                "schema_name": schema_name
            }
            
            # Call the request handler
            response = await self._request_handler(mcp_request)
            
            # Return the response
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling get schema request: {e}")
            return web.json_response(
                {
                    "status": "error",
                    "error": {
                        "code": "internal_error",
                        "message": f"Internal error: {str(e)}"
                    }
                },
                status=500
            )
    
    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running