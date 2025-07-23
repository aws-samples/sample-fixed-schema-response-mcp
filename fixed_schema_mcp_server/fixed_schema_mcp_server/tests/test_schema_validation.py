"""
Tests for schema validation functionality.
"""

import unittest

from fixed_schema_mcp_server.schema.validation import validate_against_schema, validate_with_detailed_errors

class TestSchemaValidation(unittest.TestCase):
    """Tests for schema validation functionality."""
    
    def test_validate_against_schema_valid(self):
        """Test validating valid data against a schema."""
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            }
        }
        
        data = {
            "name": "John",
            "age": 30
        }
        
        self.assertTrue(validate_against_schema(data, schema))
    
    def test_validate_against_schema_invalid(self):
        """Test validating invalid data against a schema."""
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            }
        }
        
        data = {
            "name": "John",
            "age": -1
        }
        
        self.assertFalse(validate_against_schema(data, schema))
    
    def test_validate_with_detailed_errors_valid(self):
        """Test validating valid data with detailed errors."""
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            }
        }
        
        data = {
            "name": "John",
            "age": 30
        }
        
        is_valid, errors = validate_with_detailed_errors(data, schema)
        self.assertTrue(is_valid)
        self.assertIsNone(errors)
    
    def test_validate_with_detailed_errors_invalid(self):
        """Test validating invalid data with detailed errors."""
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            }
        }
        
        data = {
            "name": "John",
            "age": -1
        }
        
        is_valid, errors = validate_with_detailed_errors(data, schema)
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)
        self.assertGreater(len(errors), 0)