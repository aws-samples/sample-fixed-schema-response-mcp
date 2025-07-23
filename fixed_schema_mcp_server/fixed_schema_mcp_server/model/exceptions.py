"""
Exceptions for model-related functionality.
"""

class ModelError(Exception):
    """Base exception for model errors."""
    pass

class ModelConnectionError(ModelError):
    """Exception raised when there is an error connecting to the model."""
    pass

class ModelResponseError(ModelError):
    """Exception raised when there is an error in the model response."""
    pass

class ModelRateLimitError(ModelError):
    """Exception raised when the model rate limit is exceeded."""
    pass