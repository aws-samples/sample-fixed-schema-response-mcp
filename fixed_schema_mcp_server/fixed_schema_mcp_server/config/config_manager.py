"""
Configuration management functionality for the Fixed Schema Response MCP Server.

This module provides functionality for loading, validating, and managing configuration.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

from fixed_schema_mcp_server.core.interfaces import ConfigManagerInterface
from fixed_schema_mcp_server.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class ConfigManager(ConfigManagerInterface):
    """
    Configuration manager for the Fixed Schema Response MCP Server.
    
    This class is responsible for loading, validating, and managing configuration.
    """
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._config = {}
        self._config_path = None
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from the specified path.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            The configuration as a dictionary
            
        Raises:
            FileNotFoundError: If the configuration file does not exist
            ConfigurationError: If the configuration is invalid
        """
        try:
            # Check if the file exists
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            # Load the configuration
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Validate the configuration
            self._validate_config(config)
            
            # Store the configuration
            self._config = config
            self._config_path = config_path
            
            logger.info(f"Loaded configuration from {config_path}")
            
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise ConfigurationError(f"Error parsing configuration file: {e}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise ConfigurationError(f"Error loading configuration: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            The current configuration as a dictionary
        """
        return self._config
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update the configuration with the specified updates.
        
        Args:
            config_updates: The configuration updates to apply
            
        Raises:
            ConfigurationError: If the updated configuration is invalid
        """
        # Create a copy of the current configuration
        updated_config = self._config.copy()
        
        # Apply the updates
        self._deep_update(updated_config, config_updates)
        
        # Validate the updated configuration
        self._validate_config(updated_config)
        
        # Store the updated configuration
        self._config = updated_config
        
        # Save the updated configuration to disk
        if self._config_path:
            try:
                with open(self._config_path, "w") as f:
                    json.dump(self._config, f, indent=2)
                
                logger.info(f"Saved updated configuration to {self._config_path}")
                
            except Exception as e:
                logger.error(f"Error saving configuration: {e}")
                raise ConfigurationError(f"Error saving configuration: {e}")
    
    def reload_config(self) -> None:
        """
        Reload configuration from disk.
        
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        if self._config_path:
            self.load_config(self._config_path)
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate the configuration.
        
        Args:
            config: The configuration to validate
            
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        # Check for required sections
        required_sections = ["server", "model", "schemas"]
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
        
        # Validate server configuration
        server_config = config.get("server", {})
        if not isinstance(server_config, dict):
            raise ConfigurationError("Server configuration must be a dictionary")
        
        # Validate model configuration
        model_config = config.get("model", {})
        if not isinstance(model_config, dict):
            raise ConfigurationError("Model configuration must be a dictionary")
        
        # Check for required model fields
        required_model_fields = ["provider"]
        for field in required_model_fields:
            if field not in model_config:
                raise ConfigurationError(f"Missing required model configuration field: {field}")
        
        # Validate schemas configuration
        schemas_config = config.get("schemas", {})
        if not isinstance(schemas_config, dict):
            raise ConfigurationError("Schemas configuration must be a dictionary")
        
        # Check for required schemas fields
        required_schemas_fields = ["path"]
        for field in required_schemas_fields:
            if field not in schemas_config:
                raise ConfigurationError(f"Missing required schemas configuration field: {field}")
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep update a dictionary.
        
        Args:
            target: The dictionary to update
            source: The dictionary with updates
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value