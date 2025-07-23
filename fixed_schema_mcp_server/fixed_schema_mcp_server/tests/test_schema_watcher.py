"""
Tests for the schema watcher module.
"""

import os
import json
import time
import pytest
import tempfile
from unittest.mock import MagicMock

from fixed_schema_mcp_server.schema.schema_watcher import SchemaWatcher


class TestSchemaWatcher:
    """Test cases for the SchemaWatcher class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test schemas
        self.temp_dir = tempfile.TemporaryDirectory()
        self.schema_path = self.temp_dir.name
        
        # Create a mock callback function
        self.mock_callback = MagicMock()
        
        # Create the schema watcher
        self.watcher = SchemaWatcher(self.schema_path, self.mock_callback)
    
    def teardown_method(self):
        """Tear down test fixtures."""
        # Stop the watcher if it's running
        if self.watcher.is_running():
            self.watcher.stop()
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_start_stop(self):
        """Test starting and stopping the watcher."""
        # Start the watcher
        self.watcher.start()
        assert self.watcher.is_running() is True
        
        # Stop the watcher
        self.watcher.stop()
        assert self.watcher.is_running() is False
    
    def test_invalid_schema_path(self):
        """Test starting the watcher with an invalid schema path."""
        # Create a watcher with a non-existent path
        watcher = SchemaWatcher("/path/does/not/exist", self.mock_callback)
        
        # Starting the watcher should raise an exception
        with pytest.raises(FileNotFoundError):
            watcher.start()
    
    def test_file_change_triggers_callback(self):
        """Test that a file change triggers the callback."""
        # Start the watcher
        self.watcher.start()
        
        # Create a test schema file
        test_schema = {
            "name": "test_schema",
            "description": "A test schema",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                }
            }
        }
        
        schema_file_path = os.path.join(self.schema_path, "test_schema.json")
        with open(schema_file_path, "w") as f:
            json.dump(test_schema, f)
        
        # Wait for the file system events to be processed
        time.sleep(2)
        
        # Check that the callback was called
        assert self.mock_callback.called
        
        # Reset the mock for the next test
        self.mock_callback.reset_mock()
        
        # Modify the schema file
        test_schema["description"] = "Updated test schema"
        with open(schema_file_path, "w") as f:
            json.dump(test_schema, f)
        
        # Wait for the file system events to be processed
        time.sleep(2)
        
        # Check that the callback was called again
        assert self.mock_callback.called
    
    def test_non_schema_file_ignored(self):
        """Test that non-schema files are ignored."""
        # Start the watcher
        self.watcher.start()
        
        # Create a non-schema file
        non_schema_file_path = os.path.join(self.schema_path, "not_a_schema.txt")
        with open(non_schema_file_path, "w") as f:
            f.write("This is not a schema file")
        
        # Wait for the file system events to be processed
        time.sleep(2)
        
        # Check that the callback was not called
        assert not self.mock_callback.called