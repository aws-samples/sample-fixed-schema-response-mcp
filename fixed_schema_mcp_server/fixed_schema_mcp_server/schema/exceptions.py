"""
Exceptions for schema-related functionality.
"""

class SchemaError(Exception):
    """Base exception for schema errors."""
    pass

class SchemaNotFoundError(SchemaError):
    """Exception raised when a schema is not found."""
    pass

class SchemaValidationError(SchemaError):
    """Exception raised when schema validation fails."""
    
    def __init__(self, message: str, errors=None):
        """
        Initialize the exception.
        
        Args:
            message: The error message
            errors: Optional validation errors
        """
        super().__init__(message)
        self.errors = errors