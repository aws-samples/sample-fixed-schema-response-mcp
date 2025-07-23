"""
Error handling functionality for the Fixed Schema Response MCP Server.

This module provides functionality for handling errors, including
error classification, retry logic, and error response generation.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Set, Tuple

from fixed_schema_mcp_server.core.exceptions import (
    MCPServerError, RequestValidationError, RequestProcessingError,
    ModelError, ConfigurationError
)
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError, SchemaValidationError

logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Error handler for the Fixed Schema Response MCP Server.
    
    This class is responsible for handling errors, including error classification,
    retry logic, and error response generation.
    """
    
    # Error categories
    CATEGORY_VALIDATION = "validation"
    CATEGORY_PROCESSING = "processing"
    CATEGORY_MODEL = "model"
    CATEGORY_SCHEMA = "schema"
    CATEGORY_CONFIGURATION = "configuration"
    CATEGORY_INTERNAL = "internal"
    
    # Error codes
    CODE_VALIDATION_ERROR = "validation_error"
    CODE_PROCESSING_ERROR = "processing_error"
    CODE_MODEL_ERROR = "model_error"
    CODE_SCHEMA_NOT_FOUND = "schema_not_found"
    CODE_SCHEMA_VALIDATION_ERROR = "schema_validation_error"
    CODE_CONFIGURATION_ERROR = "configuration_error"
    CODE_INTERNAL_ERROR = "internal_error"
    
    # Retryable error types
    RETRYABLE_ERRORS = {
        ModelError
    }
    
    def __init__(self, max_retries: int = 3, enable_monitoring: bool = True):
        """
        Initialize the error handler.
        
        Args:
            max_retries: The maximum number of retries for retryable errors
            enable_monitoring: Whether to enable error monitoring
        """
        self._max_retries = max_retries
        self._enable_monitoring = enable_monitoring
        self._error_counts = {}
        self._last_errors = {}
        self._start_time = time.time()
    
    def handle_error(self, error: Exception, request_id: Optional[str] = None, request_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an error and generate an error response.
        
        Args:
            error: The error to handle
            request_id: The ID of the request that caused the error
            request_data: The request data that caused the error
            
        Returns:
            An error response dictionary
        """
        # Log the error
        logger.error(f"Error handling request {request_id}: {error}")
        
        # Update error monitoring
        if self._enable_monitoring:
            self._update_error_monitoring(error)
        
        # Classify the error
        category, code, message, details = self._classify_error(error)
        
        # Generate the error response
        response = {
            "status": "error",
            "error": {
                "code": code,
                "message": message
            }
        }
        
        # Add details if available
        if details:
            response["error"]["details"] = details
        
        # Add request ID if available
        if request_id:
            response["error"]["request_id"] = request_id
        
        return response
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            error: The error to check
            attempt: The current attempt number
            
        Returns:
            True if the error should be retried, False otherwise
        """
        # Check if the error is retryable
        for error_type in self.RETRYABLE_ERRORS:
            if isinstance(error, error_type):
                # Check if we've reached the maximum number of retries
                return attempt < self._max_retries
        
        # Not a retryable error
        return False
    
    def _classify_error(self, error: Exception) -> Tuple[str, str, str, Optional[Dict[str, Any]]]:
        """
        Classify an error and generate error details.
        
        Args:
            error: The error to classify
            
        Returns:
            A tuple of (category, code, message, details)
        """
        # Default values
        category = self.CATEGORY_INTERNAL
        code = self.CODE_INTERNAL_ERROR
        message = str(error)
        details = None
        
        # Classify based on error type
        if isinstance(error, RequestValidationError):
            category = self.CATEGORY_VALIDATION
            code = self.CODE_VALIDATION_ERROR
        elif isinstance(error, RequestProcessingError):
            category = self.CATEGORY_PROCESSING
            code = self.CODE_PROCESSING_ERROR
        elif isinstance(error, ModelError):
            category = self.CATEGORY_MODEL
            code = self.CODE_MODEL_ERROR
        elif isinstance(error, SchemaNotFoundError):
            category = self.CATEGORY_SCHEMA
            code = self.CODE_SCHEMA_NOT_FOUND
        elif isinstance(error, SchemaValidationError):
            category = self.CATEGORY_SCHEMA
            code = self.CODE_SCHEMA_VALIDATION_ERROR
            # Extract validation details if available
            if hasattr(error, "errors"):
                details = {"validation_errors": error.errors}
        elif isinstance(error, ConfigurationError):
            category = self.CATEGORY_CONFIGURATION
            code = self.CODE_CONFIGURATION_ERROR
        
        return category, code, message, details
    
    def _update_error_monitoring(self, error: Exception) -> None:
        """
        Update error monitoring statistics.
        
        Args:
            error: The error to record
        """
        # Get the error type
        error_type = type(error).__name__
        
        # Update error counts
        if error_type not in self._error_counts:
            self._error_counts[error_type] = 0
        self._error_counts[error_type] += 1
        
        # Update last errors
        self._last_errors[error_type] = {
            "message": str(error),
            "time": time.time()
        }
    
    def get_monitoring_data(self) -> Dict[str, Any]:
        """
        Get error monitoring data.
        
        Returns:
            A dictionary containing error monitoring data
        """
        if not self._enable_monitoring:
            return {"monitoring_enabled": False}
        
        return {
            "monitoring_enabled": True,
            "uptime": time.time() - self._start_time,
            "error_counts": self._error_counts,
            "last_errors": self._last_errors
        }