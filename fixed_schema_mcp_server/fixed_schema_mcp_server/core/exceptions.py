"""
Exceptions for the Fixed Schema Response MCP Server.
"""

class MCPServerError(Exception):
    """Base exception for MCP server errors."""
    pass

class MCPLifecycleError(MCPServerError):
    """Exception for server lifecycle errors."""
    pass

class MCPRequestError(MCPServerError):
    """Exception for request handling errors."""
    pass

class MCPProtocolError(MCPServerError):
    """Exception for protocol errors."""
    pass

class MCPConnectionError(MCPServerError):
    """Exception for connection errors."""
    pass

class RequestValidationError(MCPRequestError):
    """Exception for request validation errors."""
    pass

class RequestProcessingError(MCPRequestError):
    """Exception for request processing errors."""
    pass

class ConfigurationError(MCPServerError):
    """Exception for configuration errors."""
    pass

class ModelError(MCPServerError):
    """Exception for model errors."""
    pass