"""
Tests for schema manager functionality.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from fixed_schema_mcp_server.schema.schema_manager import SchemaManager
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError

class TestSchemaManager(unittest.TestCase):
    """Tests for schema manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.schema_manager = SchemaManager()
        
        # Create a temporary directory for schemas
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test schema
        self.test_schema = {
            "name": "test_schema",
            "description": "A test schema",
            "schema": {
                "type": "object",
                "required": ["name", "age"],
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0}
                }
            },
            "system_prompt": "You are a test assistant."
        }
        
        # Write the test schema to a file
        with open(os.path.join(self.temp_dir.name, "test_schema.json"), "w") as f:
            json.dump(self.test_schema, f)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
    
    def test_load_schemas(self):
        """Test loading schemas from a directory."""
        self.schema_manager.load_schemas(self.temp_dir.name)
        self.assertEqual(self.schema_manager.get_schema_count(), 1)
    
    def test_get_schema(self):
        """Test getting a schema by name."""
        self.schema_manager.load_schemas(self.temp_dir.name)
        schema = self.schema_manager.get_schema("test_schema")
        self.assertEqual(schema.name, "test_schema")
        self.assertEqual(schema.description, "A test schema")
        self.assertEqual(schema.system_prompt, "You are a test assistant.")
    
    def test_get_schema_not_found(self):
        """Test getting a schema that doesn't exist."""
        self.schema_manager.load_schemas(self.temp_dir.name)
        with self.assertRaises(SchemaNotFoundError):
            self.schema_manager.get_schema("nonexistent_schema")
    
    def test_validate_against_schema(self):
        """Test validating data against a schema."""
        self.schema_manager.load_schemas(self.temp_dir.name)
        
        # Valid data
        valid_data = {
            "name": "John",
            "age": 30
        }
        self.assertTrue(self.schema_manager.validate_against_schema(valid_data, "test_schema"))
        
        # Invalid data
        invalid_data = {
            "name": "John",
            "age": -1
        }
        self.assertFalse(self.schema_manager.validate_against_schema(invalid_data, "test_schema"))
    
    def test_get_all_schema_names(self):
        """Test getting all schema names."""
        self.schema_manager.load_schemas(self.temp_dir.name)
        schema_names = self.schema_manager.get_all_schema_names()
        self.assertEqual(len(schema_names), 1)
        self.assertEqual(schema_names[0], "test_schema")
    
    def test_reload_schemas(self):
        """Test reloading schemas."""
        self.schema_manager.load_schemas(self.temp_dir.name)
        self.assertEqual(self.schema_manager.get_schema_count(), 1)
        
        # Add another schema
        another_schema = {
            "name": "another_schema",
            "description": "Another test schema",
            "schema": {
                "type": "object",
                "required": ["title", "content"],
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"}
                }
            }
        }
        
        # Write the schema to a file
        with open(os.path.join(self.temp_dir.name, "another_schema.json"), "w") as f:
            json.dump(another_schema, f)
        
        # Reload schemas
        self.schema_manager.reload_schemas()
        self.assertEqual(self.schema_manager.get_schema_count(), 2)