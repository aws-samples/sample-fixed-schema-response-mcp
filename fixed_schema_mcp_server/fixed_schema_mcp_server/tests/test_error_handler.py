"""
Tests for the error handler module.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from fixed_schema_mcp_server.core.error_handler import ErrorHandler
from fixed_schema_mcp_server.core.exceptions import (
    MCPServerError, MCPConnectionError, MCPProtocolError, 
    MCPRequestError, MCPLifecycleError, RequestValidationError, 
    RequestProcessingError
)
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError, SchemaValidationError
from fixed_schema_mcp_server.model.exceptions import ModelError
from fixed_schema_mcp_server.response.exceptions import ResponseProcessingError


class TestErrorHandler:
    """Test cases for the ErrorHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler(max_retries=3, enable_monitoring=True)
    
    def test_handle_error_basic(self):
        """Test handling a basic error."""
        # Create a test error
        error = Exception("Test error")
        
        # Handle the error
        response = self.error_handler.handle_error(error)
        
        # Check the response
        assert response["status"] == "error"
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert response["error"]["code"] == "internal_error"
        assert response["error"]["message"] == "Test error"
    
    def test_handle_error_with_request_id(self):
        """Test handling an error with a request ID."""
        # Create a test error
        error = Exception("Test error")
        request_id = "test-request-id"
        
        # Handle the error
        response = self.error_handler.handle_error(error, request_id=request_id)
        
        # Check the response
        assert response["status"] == "error"
        assert "error" in response
        assert "request_id" in response["error"]
        assert response["error"]["request_id"] == request_id
    
    def test_handle_specific_errors(self):
        """Test handling specific error types."""
        # Test cases for different error types
        test_cases = [
            (MCPConnectionError("Connection failed"), "connection_error"),
            (MCPProtocolError("Invalid protocol"), "protocol_error"),
            (RequestValidationError("Invalid request"), "validation_error"),
            (SchemaNotFoundError("Schema not found"), "schema_not_found"),
            (ModelError("Model error"), "model_error"),
            (json.JSONDecodeError("Invalid JSON", "{", 0), "json_decode_error")
        ]
        
        for error, expected_code in test_cases:
            response = self.error_handler.handle_error(error)
            assert response["error"]["code"] == expected_code
    
    def test_sanitize_request_data(self):
        """Test sanitizing request data."""
        # Create test request data with sensitive information
        request_data = {
            "query": "Test query",
            "schema": "test_schema",
            "api_key": "secret-api-key",
            "token": "secret-token",
            "password": "secret-password",
            "parameters": {
                "temperature": 0.7
            }
        }
        
        # Sanitize the request data
        sanitized_data = self.error_handler._sanitize_request_data(request_data)
        
        # Check that sensitive fields are redacted
        assert sanitized_data["api_key"] == "***REDACTED***"
        assert sanitized_data["token"] == "***REDACTED***"
        assert sanitized_data["password"] == "***REDACTED***"
        
        # Check that non-sensitive fields are unchanged
        assert sanitized_data["query"] == "Test query"
        assert sanitized_data["schema"] == "test_schema"
        assert sanitized_data["parameters"]["temperature"] == 0.7
    
    def test_get_error_code(self):
        """Test getting error codes for different error types."""
        # Test cases for different error types
        test_cases = [
            (Exception("Generic error"), "internal_error"),
            (ValueError("Invalid value"), "value_error"),
            (MCPServerError("Server error"), "server_error"),
            (MCPConnectionError("Connection error"), "connection_error"),
            (RequestValidationError("Validation error"), "validation_error"),
            (SchemaNotFoundError("Schema not found"), "schema_not_found"),
            (ModelError("Model error"), "model_error"),
            (ResponseProcessingError("Processing error"), "response_processing_error")
        ]
        
        for error, expected_code in test_cases:
            code = self.error_handler._get_error_code(error)
            assert code == expected_code
    
    def test_get_recovery_strategy(self):
        """Test getting recovery strategies for different error types."""
        # Test cases for different error types
        test_cases = [
            (Exception("Generic error"), None),
            (ValueError("Invalid value"), None),
            (MCPConnectionError("Connection error"), "retry"),
            (ModelError("Model error"), "retry"),
            (json.JSONDecodeError("Invalid JSON", "{", 0), "fallback")
        ]
        
        for error, expected_strategy in test_cases:
            strategy = self.error_handler.get_recovery_strategy(error)
            assert strategy == expected_strategy
    
    def test_should_retry(self):
        """Test determining if an operation should be retried."""
        # Test cases for different error types and attempt numbers
        test_cases = [
            (MCPConnectionError("Connection error"), 1, True),
            (MCPConnectionError("Connection error"), 2, True),
            (MCPConnectionError("Connection error"), 3, False),
            (ModelError("Model error"), 1, True),
            (ModelError("Model error"), 3, False),
            (Exception("Generic error"), 1, False)
        ]
        
        for error, attempt, expected_result in test_cases:
            result = self.error_handler.should_retry(error, attempt)
            assert result == expected_result
    
    def test_monitoring_data(self):
        """Test collecting and retrieving monitoring data."""
        # Handle some errors to collect monitoring data
        self.error_handler.handle_error(Exception("Error 1"))
        self.error_handler.handle_error(ValueError("Error 2"))
        self.error_handler.handle_error(MCPConnectionError("Error 3"))
        self.error_handler.handle_error(MCPConnectionError("Error 4"))
        
        # Get monitoring data
        monitoring_data = self.error_handler.get_monitoring_data()
        
        # Check monitoring data
        assert "error_counts" in monitoring_data
        assert "last_errors" in monitoring_data
        assert "total_errors" in monitoring_data
        assert monitoring_data["total_errors"] == 4
        assert monitoring_data["error_counts"]["internal_error"] == 1
        assert monitoring_data["error_counts"]["value_error"] == 1
        assert monitoring_data["error_counts"]["connection_error"] == 2
        assert len(monitoring_data["last_errors"]) == 4
    
    def test_reset_monitoring_data(self):
        """Test resetting monitoring data."""
        # Handle some errors to collect monitoring data
        self.error_handler.handle_error(Exception("Error 1"))
        self.error_handler.handle_error(ValueError("Error 2"))
        
        # Reset monitoring data
        self.error_handler.reset_monitoring_data()
        
        # Get monitoring data
        monitoring_data = self.error_handler.get_monitoring_data()
        
        # Check monitoring data
        assert monitoring_data["total_errors"] == 0
        assert len(monitoring_data["error_counts"]) == 0
        assert len(monitoring_data["last_errors"]) == 0
    
    @patch("logging.Logger.error")
    @patch("logging.Logger.warning")
    def test_log_error(self, mock_warning, mock_error):
        """Test logging errors at appropriate levels."""
        # Test cases for different error types
        test_cases = [
            (Exception("Generic error"), mock_error),
            (MCPServerError("Server error"), mock_error),
            (RequestValidationError("Validation error"), mock_warning),
            (SchemaValidationError("Schema validation error"), mock_warning)
        ]
        
        for error, mock_log in test_cases:
            # Reset mock
            mock_warning.reset_mock()
            mock_error.reset_mock()
            
            # Handle the error
            self.error_handler.handle_error(error)
            
            # Check that the appropriate log method was called
            assert mock_log.called