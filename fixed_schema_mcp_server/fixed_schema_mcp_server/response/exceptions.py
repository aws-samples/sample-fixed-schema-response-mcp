"""
Exceptions for the response module.
"""

from typing import Optional, Dict, Any


class ResponseError(Exception):
    """Base exception for response-related errors."""
    pass


class ResponseProcessingError(ResponseError):
    """Exception raised when there is an error processing a response."""
    
    def __init__(self, message: str, cause: Exception = None):
        self.cause = cause
        cause_msg = f": {str(cause)}" if cause else ""
        super().__init__(f"Response processing error: {message}{cause_msg}")


class ResponseExtractionError(ResponseError):
    """Exception raised when there is an error extracting data from a response."""
    
    def __init__(self, message: str, raw_response: Optional[str] = None, cause: Exception = None):
        self.raw_response = raw_response
        self.cause = cause
        cause_msg = f": {str(cause)}" if cause else ""
        super().__init__(f"Response extraction error: {message}{cause_msg}")


class ResponseValidationError(ResponseError):
    """Exception raised when a response fails validation."""
    
    def __init__(self, message: str, errors: Optional[list] = None, cause: Exception = None):
        self.errors = errors or []
        self.cause = cause
        cause_msg = f": {str(cause)}" if cause else ""
        super().__init__(f"Response validation error: {message}{cause_msg}")


class ResponseFixError(ResponseError):
    """Exception raised when there is an error fixing a response."""
    
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None, cause: Exception = None):
        self.response = response
        self.cause = cause
        cause_msg = f": {str(cause)}" if cause else ""
        super().__init__(f"Response fix error: {message}{cause_msg}")