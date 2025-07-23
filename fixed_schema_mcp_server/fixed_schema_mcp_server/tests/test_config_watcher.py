"""
Tests for the configuration watcher module.
"""

import os
import json
import time
import pytest
import tempfile
from unittest.mock import MagicMock, patch

from fixed_schema_mcp_server.config import ConfigManager
from fixed_schema_mcp_server.config.config_watcher import ConfigWatcher


class TestConfigWatcher:
    """Test cases for the ConfigWatcher class."""
    
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
    def config_file(self, valid_config_dict):
        """Create a temporary configuration file."""
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as temp_file:
            json.dump(valid_config_dict, temp_file)
            temp_file_path = temp_file.name
        
        yield temp_file_path
        
        # Clean up
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
    
    @pytest.fixture
    def config_manager(self):
        """Return a ConfigManager instance with mocked reload_config."""
        manager = ConfigManager()
        manager.reload_config = MagicMock()
        return manager
    
    def test_watcher_initialization(self, config_manager, config_file):
        """Test initializing the configuration watcher."""
        watcher = ConfigWatcher(config_manager, config_file)
        assert watcher._config_manager == config_manager
        assert watcher._config_path == config_file
        assert watcher._running is False
        assert watcher._thread is None
    
    def test_watcher_start_stop(self, config_manager, config_file):
        """Test starting and stopping the configuration watcher."""
        watcher = ConfigWatcher(config_manager, config_file)
        
        # Start the watcher
        watcher.start()
        assert watcher._running is True
        assert watcher._thread is not None
        thread = watcher._thread  # Save a reference to the thread
        assert thread.is_alive()
        
        # Stop the watcher
        watcher.stop()
        assert watcher._running is False
        time.sleep(0.1)  # Give the thread time to stop
        # The thread reference might be cleared in stop(), so we use our saved reference
        assert not thread.is_alive()
    
    def test_watcher_detects_changes(self, config_manager, config_file, valid_config_dict):
        """Test that the watcher detects file changes."""
        # Use a shorter poll interval for testing
        watcher = ConfigWatcher(config_manager, config_file, poll_interval=0.1)
        
        # Start the watcher
        watcher.start()
        
        try:
            # Wait a bit to ensure the watcher is running
            time.sleep(0.2)
            
            # Modify the configuration file
            valid_config_dict["server"]["port"] = 9000
            with open(config_file, 'w') as f:
                json.dump(valid_config_dict, f)
            
            # Wait for the watcher to detect the change
            time.sleep(0.3)
            
            # Check that reload_config was called
            config_manager.reload_config.assert_called_once()
            
        finally:
            # Stop the watcher
            watcher.stop()
    
    def test_watcher_handles_missing_file(self, config_manager):
        """Test that the watcher handles a missing configuration file."""
        nonexistent_file = "/path/to/nonexistent/config.json"
        
        # Use a shorter poll interval for testing
        watcher = ConfigWatcher(config_manager, nonexistent_file, poll_interval=0.1)
        
        # Start the watcher
        watcher.start()
        
        try:
            # Wait a bit to ensure the watcher is running
            time.sleep(0.3)
            
            # Check that reload_config was not called
            config_manager.reload_config.assert_not_called()
            
        finally:
            # Stop the watcher
            watcher.stop()
    
    @patch('os.path.getmtime')
    def test_watcher_handles_errors(self, mock_getmtime, config_manager, config_file):
        """Test that the watcher handles errors gracefully."""
        # Make getmtime raise an exception
        mock_getmtime.side_effect = OSError("Test error")
        
        # Use a shorter poll interval for testing
        watcher = ConfigWatcher(config_manager, config_file, poll_interval=0.1)
        
        # Start the watcher
        watcher.start()
        
        try:
            # Wait a bit to ensure the watcher is running
            time.sleep(0.3)
            
            # Check that reload_config was not called
            config_manager.reload_config.assert_not_called()
            
        finally:
            # Stop the watcher
            watcher.stop()