"""
Core interfaces for the Fixed Schema Response MCP Server.

This module defines the abstract base classes and interfaces that form the foundation
of the MCP server architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union


class MCPServerInterface(ABC):
    """Interface for the MCP server core functionality."""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the MCP server and establish connections."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the MCP server gracefully."""
        pass
    
    @abstractmethod
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming request and return a response.
        
        Args:
            request: The request data as a dictionary
            
        Returns:
            A dictionary containing the response data
        """
        pass


class SchemaManagerInterface(ABC):
    """Interface for schema management functionality."""
    
    @abstractmethod
    def load_schemas(self, schema_path: str) -> None:
        """
        Load schemas from the specified path.
        
        Args:
            schema_path: Path to the schema definitions
        """
        pass
    
    @abstractmethod
    def get_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Get a schema by name.
        
        Args:
            schema_name: Name of the schema to retrieve
            
        Returns:
            The schema definition as a dictionary
            
        Raises:
            SchemaNotFoundError: If the schema does not exist
        """
        pass
    
    @abstractmethod
    def validate_against_schema(self, data: Dict[str, Any], schema_name: str) -> bool:
        """
        Validate data against a schema.
        
        Args:
            data: The data to validate
            schema_name: Name of the schema to validate against
            
        Returns:
            True if the data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def reload_schemas(self) -> None:
        """Reload schemas from disk."""
        pass


class ModelManagerInterface(ABC):
    """Interface for model management functionality."""
    
    @abstractmethod
    async def generate_response(self, prompt: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            parameters: Optional model parameters to override defaults
            
        Returns:
            The generated response as a string
        """
        pass
    
    @abstractmethod
    def set_model_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Update model parameters.
        
        Args:
            parameters: The parameters to update
        """
        pass


class ResponseProcessorInterface(ABC):
    """Interface for response processing functionality."""
    
    @abstractmethod
    async def process_response(self, raw_response: str, schema_name: str) -> Dict[str, Any]:
        """
        Process and format the raw response according to the schema.
        
        Args:
            raw_response: The raw response from the model
            schema_name: The name of the schema to format against
            
        Returns:
            The processed response as a dictionary
        """
        pass
    
    @abstractmethod
    def validate_response(self, processed_response: Dict[str, Any], schema_name: str) -> bool:
        """
        Validate the processed response against the schema.
        
        Args:
            processed_response: The processed response to validate
            schema_name: The name of the schema to validate against
            
        Returns:
            True if the response is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def fix_response(self, response: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """
        Attempt to fix a response that doesn't conform to the schema.
        
        Args:
            response: The response to fix
            schema_name: The name of the schema to fix against
            
        Returns:
            The fixed response as a dictionary
        """
        pass


class ConfigManagerInterface(ABC):
    """Interface for configuration management functionality."""
    
    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from the specified path.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            The configuration as a dictionary
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            The current configuration as a dictionary
        """
        pass
    
    @abstractmethod
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update the configuration with the specified updates.
        
        Args:
            config_updates: The configuration updates to apply
        """
        pass
    
    @abstractmethod
    def reload_config(self) -> None:
        """Reload configuration from disk."""
        pass