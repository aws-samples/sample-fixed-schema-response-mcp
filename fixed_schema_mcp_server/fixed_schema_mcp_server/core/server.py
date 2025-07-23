"""
MCP server implementation for the Fixed Schema Response MCP Server.

This module provides the MCPServer class that implements the core MCP server
functionality, including request handling, lifecycle management, and
integration with other components.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Dict, Any, Optional, List, Union, Callable, Awaitable

from fixed_schema_mcp_server.core.interfaces import MCPServerInterface
from fixed_schema_mcp_server.core.protocol import MCPProtocolHandler
from fixed_schema_mcp_server.core.http_server import HTTPServer
from fixed_schema_mcp_server.core.exceptions import MCPServerError, MCPLifecycleError, MCPRequestError, RequestValidationError, RequestProcessingError
from fixed_schema_mcp_server.core.request_queue import QueueFullError
from fixed_schema_mcp_server.core.request_processor import RequestProcessor
from fixed_schema_mcp_server.core.error_handler import ErrorHandler
from fixed_schema_mcp_server.config.config_manager import ConfigManager
from fixed_schema_mcp_server.schema.schema_manager import SchemaManager
from fixed_schema_mcp_server.model.model_manager import ModelManager
from fixed_schema_mcp_server.response.response_processor import ResponseProcessor
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError
from fixed_schema_mcp_server.model.exceptions import ModelError

logger = logging.getLogger(__name__)


class MCPServer(MCPServerInterface):
    """
    Implementation of the MCP server interface.
    
    This class is responsible for handling MCP requests, managing the server
    lifecycle, and coordinating the various components of the system.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the MCP server.
        
        Args:
            config_path: Path to the configuration file
            
        Raises:
            FileNotFoundError: If the configuration file does not exist
            ValueError: If the configuration is invalid
        """
        self._config_path = config_path
        self._protocol_handler = MCPProtocolHandler()
        self._config_manager = ConfigManager()
        self._schema_manager = SchemaManager()
        self._model_manager = None
        self._response_processor = None
        self._request_processor = None
        self._error_handler = None
        self._http_server = None
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Load the configuration
        self._config = self._config_manager.load_config(config_path)
        
        # Initialize components
        self._initialize_components()
        
        # Register request handlers
        self._register_request_handlers()
        
        logger.info("MCP server initialized")
    
    def _initialize_components(self) -> None:
        """
        Initialize the server components based on the configuration.
        
        Raises:
            ValueError: If the configuration is invalid
        """
        # Get configuration sections
        server_config = self._config.get("server", {})
        model_config = self._config.get("model", {})
        schema_config = self._config.get("schemas", {})
        error_config = self._config.get("error_handling", {})
        
        # Initialize schema manager
        schema_path = schema_config.get("path", "./schemas")
        if not os.path.exists(schema_path):
            logger.warning(f"Schema path '{schema_path}' does not exist, creating it")
            os.makedirs(schema_path, exist_ok=True)
        
        self._schema_manager.load_schemas(schema_path)
        logger.info(f"Loaded {self._schema_manager.get_schema_count()} schemas from {schema_path}")
        
        # Initialize model manager
        self._model_manager = ModelManager(model_config)
        
        # Initialize response processor
        self._response_processor = ResponseProcessor(self._schema_manager)
        
        # Initialize error handler
        max_retries = error_config.get("max_retries", 3)
        enable_monitoring = error_config.get("enable_monitoring", True)
        self._error_handler = ErrorHandler(
            max_retries=max_retries,
            enable_monitoring=enable_monitoring
        )
        
        # Get performance configuration
        performance_config = self._config.get("performance", {})
        rate_limit = performance_config.get("rate_limit", 10.0)
        rate_period = performance_config.get("rate_period", 60.0)
        burst_limit = performance_config.get("burst_limit", None)
        max_queue_size = performance_config.get("max_queue_size", 100)
        enable_queue = performance_config.get("enable_queue", True)
        
        # Initialize request processor
        self._request_processor = RequestProcessor(
            model_manager=self._model_manager,
            schema_manager=self._schema_manager,
            response_processor=self._response_processor,
            rate_limit=rate_limit,
            rate_period=rate_period,
            burst_limit=burst_limit,
            max_queue_size=max_queue_size,
            enable_queue=enable_queue
        )
        
        # Initialize HTTP server
        host = server_config.get("host", "localhost")
        port = server_config.get("port", 8000)
        self._http_server = HTTPServer(host=host, port=port)
        self._http_server.set_request_handler(self.handle_request)
        
        logger.info("Server components initialized")
    
    def _register_request_handlers(self) -> None:
        """Register handlers for different request types."""
        # Register the main request handler with the protocol handler
        self._protocol_handler.register_request_handler("request", self.handle_request)
        
        logger.info("Request handlers registered")
    
    async def start(self) -> None:
        """
        Start the MCP server and establish connections.
        
        Raises:
            MCPLifecycleError: If there is an error starting the server
        """
        if self._running:
            logger.warning("MCP server is already running")
            return
        
        try:
            # Set up signal handlers for graceful shutdown
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._handle_signal(s))
                )
            
            # Start the protocol handler
            await self._protocol_handler.initialize()
            await self._protocol_handler.start()
            
            # Start the model manager
            await self._model_manager.start()
            
            # Start the request processor
            await self._request_processor.start()
            
            # Start the HTTP server
            await self._http_server.start()
            
            self._running = True
            logger.info("MCP server started")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise MCPLifecycleError(f"Failed to start server: {e}")
    
    async def stop(self) -> None:
        """
        Stop the MCP server gracefully.
        
        Raises:
            MCPLifecycleError: If there is an error stopping the server
        """
        if not self._running:
            logger.warning("MCP server is not running")
            return
        
        try:
            # Stop the HTTP server
            await self._http_server.stop()
            
            # Stop the protocol handler
            await self._protocol_handler.stop()
            
            # Stop the request processor
            await self._request_processor.stop()
            
            # Stop the model manager
            await self._model_manager.stop()
            
            # Set the shutdown event to signal any waiting tasks
            self._shutdown_event.set()
            
            self._running = False
            logger.info("MCP server stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop MCP server: {e}")
            raise MCPLifecycleError(f"Failed to stop server: {e}")
    
    async def _handle_signal(self, sig: signal.Signals) -> None:
        """
        Handle a signal.
        
        Args:
            sig: The signal received
        """
        logger.info(f"Received signal {sig.name}, shutting down")
        await self.stop()
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming request and return a response.
        
        Args:
            request: The request data as a dictionary
            
        Returns:
            A dictionary containing the response data
            
        Raises:
            MCPRequestError: If there is an error processing the request
        """
        if not self._running:
            return {
                "status": "error",
                "error": {
                    "code": "server_not_running",
                    "message": "Server is not running"
                }
            }
        
        # Extract request ID if available
        request_id = request.get("id") if isinstance(request, dict) else None
        
        # Process the request through the request processor pipeline
        try:
            # Try to process the request
            return await self._process_request_with_retry(request, request_id)
        except QueueFullError as e:
            # Handle queue full errors
            logger.warning(f"Request queue is full: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "queue_full",
                    "message": "Request queue is full, try again later",
                    "details": {
                        "queue_metrics": self._request_processor.get_queue_metrics()
                    }
                }
            }
        except Exception as e:
            # Handle any unhandled exceptions
            return self._error_handler.handle_error(e, request_id, request)
    
    async def _process_request_with_retry(self, request: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a request with retry logic for recoverable errors.
        
        Args:
            request: The request data
            request_id: The ID of the request
            
        Returns:
            The response data
            
        Raises:
            Exception: If the request cannot be processed after retries
            QueueFullError: If the queue is full and cannot accept more requests
        """
        max_attempts = self._error_handler._max_retries
        attempt = 0
        
        while True:
            attempt += 1
            try:
                # Try to process the request
                return await self._request_processor.process_request(request, request_id)
            except QueueFullError:
                # Don't retry queue full errors, just propagate them
                raise
            except Exception as e:
                # Check if we should retry
                if self._error_handler.should_retry(e, attempt) and attempt < max_attempts:
                    logger.warning(f"Retrying request after error: {e} (attempt {attempt}/{max_attempts})")
                    # Add exponential backoff if needed
                    await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
                    continue
                
                # If we shouldn't retry or have reached max attempts, re-raise the exception
                raise
    
    async def _handle_generate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a generate request.
        
        Args:
            request: The request data
            
        Returns:
            The response data
            
        Raises:
            MCPRequestError: If there is an error processing the request
        """
        try:
            # Validate the request
            if "query" not in request:
                raise MCPRequestError("Generate request missing 'query' field")
            
            if "schema" not in request:
                raise MCPRequestError("Generate request missing 'schema' field")
            
            query = request["query"]
            schema_name = request["schema"]
            parameters = request.get("parameters", {})
            
            # Get the schema
            try:
                schema = self._schema_manager.get_schema(schema_name)
            except SchemaNotFoundError:
                raise MCPRequestError(f"Schema not found: {schema_name}")
            
            # Prepare the prompt
            system_prompt = schema.system_prompt if hasattr(schema, "system_prompt") else ""
            prompt = f"{system_prompt}\n\nUser query: {query}\n\nRespond with a JSON object that follows this schema:\n{json.dumps(schema.schema.dict() if hasattr(schema.schema, 'dict') else schema.schema.model_dump(), indent=2)}"
            
            # Generate the response
            start_time = asyncio.get_event_loop().time()
            raw_response = await self._model_manager.generate_response(prompt, parameters)
            
            # Process the response
            processed_response = await self._response_processor.process_response(raw_response, schema_name)
            
            # Calculate processing time
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Get model info
            model_info = self._model_manager.get_model_info()
            
            # Return the response
            return {
                "status": "success",
                "data": processed_response,
                "metadata": {
                    "model": model_info.get("model", "unknown"),
                    "processing_time": round(processing_time, 2)
                }
            }
            
        except SchemaNotFoundError as e:
            logger.error(f"Schema not found: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "schema_not_found",
                    "message": str(e)
                }
            }
        except ModelError as e:
            logger.error(f"Model error: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "model_error",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error handling generate request: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_validate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a validate request.
        
        Args:
            request: The request data
            
        Returns:
            The response data
            
        Raises:
            MCPRequestError: If there is an error processing the request
        """
        try:
            # Validate the request
            if "data" not in request:
                raise MCPRequestError("Validate request missing 'data' field")
            
            if "schema" not in request:
                raise MCPRequestError("Validate request missing 'schema' field")
            
            data = request["data"]
            schema_name = request["schema"]
            
            # Validate the data against the schema
            is_valid = self._schema_manager.validate_against_schema(data, schema_name)
            
            # Get detailed validation results if not valid
            validation_details = None
            if not is_valid:
                _, errors = self._schema_manager.validate_with_detailed_errors(data, schema_name)
                validation_details = errors
            
            # Return the response
            return {
                "status": "success",
                "valid": is_valid,
                "errors": validation_details if not is_valid else None
            }
            
        except SchemaNotFoundError as e:
            logger.error(f"Schema not found: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "schema_not_found",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error handling validate request: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_list_schemas_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a list_schemas request.
        
        Args:
            request: The request data
            
        Returns:
            The response data
        """
        try:
            # Get all schema names
            schema_names = self._schema_manager.get_all_schema_names()
            
            # Return the response
            return {
                "status": "success",
                "schemas": schema_names
            }
            
        except Exception as e:
            logger.error(f"Error handling list_schemas request: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_get_schema_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a get_schema request.
        
        Args:
            request: The request data
            
        Returns:
            The response data
            
        Raises:
            MCPRequestError: If there is an error processing the request
        """
        try:
            # Validate the request
            if "name" not in request:
                raise MCPRequestError("Get schema request missing 'name' field")
            
            schema_name = request["name"]
            
            # Get the schema
            try:
                schema = self._schema_manager.get_schema(schema_name)
                
                # Convert the schema to a dictionary
                schema_dict = {
                    "name": schema.name,
                    "description": schema.description,
                    "schema": schema.schema.dict() if hasattr(schema.schema, 'dict') else schema.schema.model_dump(),
                    "system_prompt": schema.system_prompt if hasattr(schema, "system_prompt") else ""
                }
                
                # Return the response
                return {
                    "status": "success",
                    "schema": schema_dict
                }
                
            except SchemaNotFoundError:
                return {
                    "status": "error",
                    "error": {
                        "code": "schema_not_found",
                        "message": f"Schema not found: {schema_name}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling get_schema request: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_health_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a health request.
        
        Args:
            request: The request data
            
        Returns:
            The response data
        """
        try:
            # Check model health
            model_health = await self._model_manager.check_model_health()
            
            # Return the response
            return {
                "status": "success",
                "health": {
                    "server": {
                        "status": "healthy",
                        "uptime": 0  # Placeholder for future implementation
                    },
                    "model": model_health
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling health request: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running
    
    def get_error_monitoring_data(self) -> Dict[str, Any]:
        """
        Get error monitoring data.
        
        Returns:
            A dictionary containing error monitoring data
        """
        if not self._error_handler:
            return {"error": "Error handler not initialized"}
        
        return self._error_handler.get_monitoring_data()