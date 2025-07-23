"""
Tests for the configuration management module.
"""

import os
import json
import yaml
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from fixed_schema_mcp_server.config import ConfigManager, ConfigModel
from fixed_schema_mcp_server.config.config_manager import ConfigError


class TestConfigManager:
    """Test cases for the ConfigManager class."""
    
    @pytest.fixture
    def valid_config_dict(self):
        """Return a valid configuration dictionary."""
        return {
            "server": {
                "host": "localhost",
                "port": 8000,
                "log_level": "info"
            },
            "model": {
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "test-api-key",
                "parameters": {
                    "temperature": 0.7,
                    "top_p": 1.0,
                    "max_tokens": 1000
                }
            },
            "schemas": {
                "path": "./schemas",
                "default_schema": "default"
            }
        }
    
    @pytest.fixture
    def config_manager(self):
        """Return a ConfigManager instance."""
        return ConfigManager()
    
    def test_load_json_config(self, config_manager, valid_config_dict):
        """Test loading a JSON configuration file."""
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as temp_file:
            json.dump(valid_config_dict, temp_file)
            temp_file_path = temp_file.name
        
        try:
            config = config_manager.load_config(temp_file_path)
            assert config["server"]["host"] == "localhost"
            assert config["model"]["provider"] == "openai"
            assert config["schemas"]["path"] == "./schemas"
        finally:
            os.unlink(temp_file_path)
    
    def test_load_yaml_config(self, config_manager, valid_config_dict):
        """Test loading a YAML configuration file."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as temp_file:
            yaml.dump(valid_config_dict, temp_file)
            temp_file_path = temp_file.name
        
        try:
            config = config_manager.load_config(temp_file_path)
            assert config["server"]["host"] == "localhost"
            assert config["model"]["provider"] == "openai"
            assert config["schemas"]["path"] == "./schemas"
        finally:
            os.unlink(temp_file_path)
    
    def test_load_invalid_format(self, config_manager):
        """Test loading a configuration file with an invalid format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as temp_file:
            temp_file.write("This is not a valid config file")
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(ConfigError):
                config_manager.load_config(temp_file_path)
        finally:
            os.unlink(temp_file_path)
    
    def test_load_nonexistent_file(self, config_manager):
        """Test loading a nonexistent configuration file."""
        with pytest.raises(ConfigError):
            config_manager.load_config("/path/to/nonexistent/config.json")
    
    def test_load_invalid_json(self, config_manager):
        """Test loading an invalid JSON configuration file."""
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as temp_file:
            temp_file.write("{invalid json")
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(ConfigError):
                config_manager.load_config(temp_file_path)
        finally:
            os.unlink(temp_file_path)
    
    def test_load_missing_required_section(self, config_manager, valid_config_dict):
        """Test loading a configuration file with a missing required section."""
        del valid_config_dict["model"]
        
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as temp_file:
            json.dump(valid_config_dict, temp_file)
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(ConfigError):
                config_manager.load_config(temp_file_path)
        finally:
            os.unlink(temp_file_path)
    
    def test_get_config_without_loading(self, config_manager):
        """Test getting configuration without loading it first."""
        with pytest.raises(ConfigError):
            config_manager.get_config()
    
    def test_update_config(self, config_manager, valid_config_dict):
        """Test updating configuration."""
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as temp_file:
            json.dump(valid_config_dict, temp_file)
            temp_file_path = temp_file.name
        
        try:
            config_manager.load_config(temp_file_path)
            
            # Update configuration
            updates = {
                "server": {
                    "port": 9000,
                    "log_level": "debug"
                },
                "model": {
                    "parameters": {
                        "temperature": 0.5
                    }
                }
            }
            
            config_manager.update_config(updates)
            
            # Check updated values
            config = config_manager.get_config()
            assert config["server"]["port"] == 9000
            assert config["server"]["log_level"] == "debug"
            assert config["model"]["parameters"]["temperature"] == 0.5
            
            # Check that other values are preserved
            assert config["server"]["host"] == "localhost"
            assert config["model"]["provider"] == "openai"
            assert config["schemas"]["path"] == "./schemas"
        finally:
            os.unlink(temp_file_path)
    
    def test_update_config_without_loading(self, config_manager):
        """Test updating configuration without loading it first."""
        with pytest.raises(ConfigError):
            config_manager.update_config({"server": {"port": 9000}})
    
    def test_reload_config(self, config_manager, valid_config_dict):
        """Test reloading configuration."""
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as temp_file:
            json.dump(valid_config_dict, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Load initial configuration
            config_manager.load_config(temp_file_path)
            
            # Modify the file
            valid_config_dict["server"]["port"] = 9000
            with open(temp_file_path, 'w') as f:
                json.dump(valid_config_dict, f)
            
            # Reload configuration
            config_manager.reload_config()
            
            # Check that the configuration was reloaded
            config = config_manager.get_config()
            assert config["server"]["port"] == 9000
        finally:
            os.unlink(temp_file_path)
    
    def test_reload_config_without_loading(self, config_manager):
        """Test reloading configuration without loading it first."""
        with pytest.raises(ConfigError):
            config_manager.reload_config()
    
    def test_change_listeners(self, config_manager, valid_config_dict):
        """Test configuration change listeners."""
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as temp_file:
            json.dump(valid_config_dict, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Load initial configuration
            config_manager.load_config(temp_file_path)
            
            # Add change listener
            listener = MagicMock()
            config_manager.add_change_listener(listener)
            
            # Update configuration
            config_manager.update_config({"server": {"port": 9000}})
            
            # Check that the listener was called
            listener.assert_called_once()
            
            # Remove listener
            config_manager.remove_change_listener(listener)
            
            # Update configuration again
            config_manager.update_config({"server": {"port": 8000}})
            
            # Check that the listener was not called again
            listener.assert_called_once()
        finally:
            os.unlink(temp_file_path)