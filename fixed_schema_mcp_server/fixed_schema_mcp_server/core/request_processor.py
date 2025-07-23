"""
Request processing functionality for the Fixed Schema Response MCP Server.

This module provides functionality for processing incoming requests,
validating them, routing them to appropriate handlers, and generating responses.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union, Callable, Awaitable

from fixed_schema_mcp_server.core.interfaces import ModelManagerInterface, SchemaManagerInterface, ResponseProcessorInterface
from fixed_schema_mcp_server.core.exceptions import RequestValidationError, RequestProcessingError
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError
from fixed_schema_mcp_server.core.request_queue import RequestQueue, QueueFullError

logger = logging.getLogger(__name__)


class RequestProcessor:
    """
    Request processor for the Fixed Schema Response MCP Server.
    
    This class is responsible for processing incoming requests,
    validating them, routing them to appropriate handlers,
    and generating responses.
    """
    
    # Request types
    GENERATE_RESPONSE = "generate_response"
    GET_SCHEMAS = "get_schemas"
    GET_SCHEMA = "get_schema"
    
    # Priority levels
    PRIORITY_HIGH = 0
    PRIORITY_NORMAL = 50
    PRIORITY_LOW = 100
    
    def __init__(
        self,
        model_manager: ModelManagerInterface,
        schema_manager: SchemaManagerInterface,
        response_processor: ResponseProcessorInterface,
        rate_limit: float = 10.0,
        rate_period: float = 60.0,
        burst_limit: Optional[int] = None,
        max_queue_size: int = 100,
        enable_queue: bool = True
    ):
        """
        Initialize the request processor.
        
        Args:
            model_manager: The model manager to use for generating responses
            schema_manager: The schema manager to use for schema operations
            response_processor: The response processor to use for processing responses
            rate_limit: The rate limit for requests (requests per rate_period)
            rate_period: The time period for the rate limit (in seconds)
            burst_limit: The maximum number of requests that can be processed in a burst
            max_queue_size: The maximum size of the queue
            enable_queue: Whether to enable request queuing
        """
        self._model_manager = model_manager
        self._schema_manager = schema_manager
        self._response_processor = response_processor
        self._request_handlers = {
            self.GENERATE_RESPONSE: self._handle_generate_response,
            self.GET_SCHEMAS: self._handle_get_schemas,
            self.GET_SCHEMA: self._handle_get_schema
        }
        
        # Initialize request queue
        self._enable_queue = enable_queue
        self._request_queue = RequestQueue(
            rate_limit=rate_limit,
            rate_period=rate_period,
            burst_limit=burst_limit,
            max_queue_size=max_queue_size
        )
        
        # Request priority mapping
        self._request_priority = {
            self.GENERATE_RESPONSE: self.PRIORITY_NORMAL,
            self.GET_SCHEMAS: self.PRIORITY_HIGH,
            self.GET_SCHEMA: self.PRIORITY_HIGH
        }
    
    async def start(self) -> None:
        """Start the request processor."""
        if self._enable_queue:
            await self._request_queue.start()
            logger.info("Request processor started with queue enabled")
        else:
            logger.info("Request processor started with queue disabled")
    
    async def stop(self) -> None:
        """Stop the request processor."""
        if self._enable_queue:
            await self._request_queue.stop()
            logger.info("Request processor stopped")
    
    async def process_request(self, request: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process an incoming request and return a response.
        
        Args:
            request: The request data as a dictionary
            request_id: Optional request ID for tracking
            
        Returns:
            A dictionary containing the response data
            
        Raises:
            RequestValidationError: If the request is invalid
            RequestProcessingError: If there is an error processing the request
            QueueFullError: If the queue is full and cannot accept more requests
        """
        try:
            # Validate the request
            self._validate_request(request)
            
            # Get the request type
            request_type = request.get("request_type")
            
            # Determine priority based on request type
            priority = self._request_priority.get(request_type, self.PRIORITY_NORMAL)
            
            # If queuing is enabled, enqueue the request
            if self._enable_queue:
                try:
                    # For non-generate requests, we can bypass the queue for better responsiveness
                    if request_type != self.GENERATE_RESPONSE:
                        handler = self._request_handlers[request_type]
                        return await handler(request)
                    
                    # For generate requests, use the queue
                    logger.debug(f"Enqueueing request {request_id} with priority {priority}")
                    queue_result = await self._request_queue.enqueue(
                        request_data=request,
                        priority=priority,
                        request_id=request_id
                    )
                    
                    # Process the request after it's dequeued
                    dequeued_request = queue_result["request_data"]
                    dequeued_request_type = dequeued_request.get("request_type")
                    
                    if dequeued_request_type in self._request_handlers:
                        handler = self._request_handlers[dequeued_request_type]
                        response = await handler(dequeued_request)
                        
                        # Add queue metrics to the response metadata
                        if "metadata" not in response:
                            response["metadata"] = {}
                        
                        response["metadata"]["queue_wait_time"] = queue_result["wait_time"]
                        response["metadata"]["queue_position"] = queue_result.get("queue_position", 0)
                        
                        return response
                    else:
                        logger.warning(f"Unsupported request type after dequeuing: {dequeued_request_type}")
                        raise RequestValidationError(f"Unsupported request type: {dequeued_request_type}")
                
                except QueueFullError as e:
                    logger.warning(f"Request queue is full: {e}")
                    raise
            else:
                # If queuing is disabled, process the request directly
                if request_type in self._request_handlers:
                    handler = self._request_handlers[request_type]
                    return await handler(request)
                else:
                    logger.warning(f"Unsupported request type: {request_type}")
                    raise RequestValidationError(f"Unsupported request type: {request_type}")
                
        except RequestValidationError as e:
            # Re-raise validation errors
            logger.warning(f"Request validation error: {e}")
            raise
        except QueueFullError:
            # Re-raise queue full errors
            raise
        except Exception as e:
            # Wrap other exceptions in RequestProcessingError
            logger.error(f"Error processing request: {e}")
            raise RequestProcessingError(f"Error processing request: {e}")
    
    def get_queue_metrics(self) -> Dict[str, Any]:
        """
        Get queue metrics.
        
        Returns:
            A dictionary containing queue metrics
        """
        if self._enable_queue:
            return self._request_queue.get_metrics()
        else:
            return {"queue_enabled": False}
    
    def _validate_request(self, request: Dict[str, Any]) -> None:
        """
        Validate an incoming request.
        
        Args:
            request: The request data to validate
            
        Raises:
            RequestValidationError: If the request is invalid
        """
        # Check if the request is a dictionary
        if not isinstance(request, dict):
            raise RequestValidationError("Request must be a dictionary")
        
        # Check if the request has a request_type field
        if "request_type" not in request:
            raise RequestValidationError("Request missing 'request_type' field")
        
        request_type = request.get("request_type")
        
        # Validate based on request type
        if request_type == self.GENERATE_RESPONSE:
            self._validate_generate_response_request(request)
        elif request_type == self.GET_SCHEMA:
            self._validate_get_schema_request(request)
        # GET_SCHEMAS doesn't need additional validation
    
    def _validate_generate_response_request(self, request: Dict[str, Any]) -> None:
        """
        Validate a generate_response request.
        
        Args:
            request: The request data to validate
            
        Raises:
            RequestValidationError: If the request is invalid
        """
        # Check if the request has a query field
        if "query" not in request:
            raise RequestValidationError("generate_response request missing 'query' field")
        
        # Check if the query is a string
        if not isinstance(request.get("query"), str):
            raise RequestValidationError("'query' field must be a string")
        
        # Check if the request has a schema field
        if "schema" not in request:
            raise RequestValidationError("generate_response request missing 'schema' field")
        
        # Check if the schema is a string
        if not isinstance(request.get("schema"), str):
            raise RequestValidationError("'schema' field must be a string")
        
        # Check if the parameters field is a dictionary if present
        if "parameters" in request and not isinstance(request.get("parameters"), dict):
            raise RequestValidationError("'parameters' field must be a dictionary")
    
    def _validate_get_schema_request(self, request: Dict[str, Any]) -> None:
        """
        Validate a get_schema request.
        
        Args:
            request: The request data to validate
            
        Raises:
            RequestValidationError: If the request is invalid
        """
        # Check if the request has a schema_name field
        if "schema_name" not in request:
            raise RequestValidationError("get_schema request missing 'schema_name' field")
        
        # Check if the schema_name is a string
        if not isinstance(request.get("schema_name"), str):
            raise RequestValidationError("'schema_name' field must be a string")
    
    async def _handle_generate_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a generate_response request.
        
        Args:
            request: The request data
            
        Returns:
            A dictionary containing the response data
            
        Raises:
            RequestProcessingError: If there is an error processing the request
            SchemaNotFoundError: If the schema does not exist
        """
        try:
            # Extract request data
            query = request.get("query")
            schema_name = request.get("schema")
            parameters = request.get("parameters", {})
            
            # Check if the schema exists
            schema = self._schema_manager.get_schema(schema_name)
            
            # Prepare the prompt with system prompt from schema if available
            system_prompt = schema.system_prompt if hasattr(schema, "system_prompt") else ""
            
            # Add schema information to the prompt
            schema_json = json.dumps(schema.schema, indent=2) if hasattr(schema, "schema") else "{}"
            
            # Create a more explicit prompt for structured output
            structured_prompt = f"""
I need you to provide information about the following query in a specific JSON format.

Query: {query}

Please format your response as a valid JSON object that follows this schema:
{schema_json}

DO NOT include any explanations, markdown formatting, or text outside the JSON structure.
ONLY respond with a valid JSON object that matches the schema.
"""
            
            # Combine system prompt and structured prompt
            prompt = f"{system_prompt}\n\n{structured_prompt}" if system_prompt else structured_prompt
            
            # Add schema name to parameters
            if "parameters" not in parameters:
                parameters["parameters"] = {}
            parameters["parameters"]["schema"] = schema_name
            
            # Generate a response from the model
            start_time = __import__("time").time()
            raw_response = await self._model_manager.generate_response(prompt, parameters)
            
            # Process the response according to the schema
            processed_response = await self._response_processor.process_response(raw_response, schema_name)
            
            # Calculate processing time
            processing_time = __import__("time").time() - start_time
            
            # Return the response
            return {
                "status": "success",
                "data": processed_response,
                "metadata": {
                    "model": parameters.get("model", "default"),
                    "processing_time": round(processing_time, 2)
                }
            }
            
        except SchemaNotFoundError as e:
            # Re-raise SchemaNotFoundError to maintain the original error type
            logger.error(f"Schema not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error handling generate_response request: {e}")
            raise RequestProcessingError(f"Error handling generate_response request: {e}")
    
    async def _handle_get_schemas(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a get_schemas request.
        
        Args:
            request: The request data
            
        Returns:
            A dictionary containing the response data
            
        Raises:
            RequestProcessingError: If there is an error processing the request
        """
        try:
            # Get all schema names
            schema_names = self._schema_manager.get_all_schema_names()
            
            # Return the schema names
            return {
                "status": "success",
                "data": {
                    "schemas": schema_names
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling get_schemas request: {e}")
            raise RequestProcessingError(f"Error handling get_schemas request: {e}")
    
    async def _handle_get_schema(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a get_schema request.
        
        Args:
            request: The request data
            
        Returns:
            A dictionary containing the response data
            
        Raises:
            RequestProcessingError: If there is an error processing the request
            SchemaNotFoundError: If the schema does not exist
        """
        try:
            # Extract request data
            schema_name = request.get("schema_name")
            
            # Get the schema
            schema = self._schema_manager.get_schema(schema_name)
            
            # Convert the schema to a dictionary
            schema_dict = schema.model_dump() if hasattr(schema, "model_dump") else schema.dict()
            
            # Return the schema
            return {
                "status": "success",
                "data": {
                    "schema": schema_dict
                }
            }
            
        except SchemaNotFoundError as e:
            # Re-raise SchemaNotFoundError to maintain the original error type
            logger.error(f"Schema not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error handling get_schema request: {e}")
            raise RequestProcessingError(f"Error handling get_schema request: {e}")