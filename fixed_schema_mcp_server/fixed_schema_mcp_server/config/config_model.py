"""
Configuration model classes for the Fixed Schema Response MCP Server.

This module defines the data models for the server configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class ServerConfig:
    """Server configuration settings."""
    host: str = "localhost"
    port: int = 8000
    log_level: str = "info"


@dataclass
class ModelConfig:
    """Model configuration settings."""
    provider: str
    model_name: str
    api_key: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default parameters if not provided."""
        if not self.parameters:
            self.parameters = {
                "temperature": 0.7,
                "top_p": 1.0,
                "max_tokens": 1000
            }


@dataclass
class SchemaConfig:
    """Schema configuration settings."""
    path: str
    default_schema: str = "default"


@dataclass
class ConfigModel:
    """Main configuration model."""
    server: ServerConfig
    model: ModelConfig
    schemas: SchemaConfig

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ConfigModel':
        """
        Create a ConfigModel instance from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            A ConfigModel instance
            
        Raises:
            ValueError: If required configuration values are missing
        """
        # Validate required sections
        required_sections = ["server", "model", "schemas"]
        for section in required_sections:
            if section not in config_dict:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Create server config
        server_dict = config_dict["server"]
        server_config = ServerConfig(
            host=server_dict.get("host", "localhost"),
            port=server_dict.get("port", 8000),
            log_level=server_dict.get("log_level", "info")
        )
        
        # Create model config
        model_dict = config_dict["model"]
        # Validate required model fields
        required_model_fields = ["provider", "model_name", "api_key"]
        for field in required_model_fields:
            if field not in model_dict:
                raise ValueError(f"Missing required model configuration field: {field}")
                
        model_config = ModelConfig(
            provider=model_dict["provider"],
            model_name=model_dict["model_name"],
            api_key=model_dict["api_key"],
            parameters=model_dict.get("parameters", {})
        )
        
        # Create schema config
        schema_dict = config_dict["schemas"]
        # Validate required schema fields
        if "path" not in schema_dict:
            raise ValueError("Missing required schema configuration field: path")
            
        schema_config = SchemaConfig(
            path=schema_dict["path"],
            default_schema=schema_dict.get("default_schema", "default")
        )
        
        return cls(
            server=server_config,
            model=model_config,
            schemas=schema_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ConfigModel to a dictionary.
        
        Returns:
            A dictionary representation of the configuration
        """
        return {
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "log_level": self.server.log_level
            },
            "model": {
                "provider": self.model.provider,
                "model_name": self.model.model_name,
                "api_key": self.model.api_key,
                "parameters": self.model.parameters
            },
            "schemas": {
                "path": self.schemas.path,
                "default_schema": self.schemas.default_schema
            }
        }