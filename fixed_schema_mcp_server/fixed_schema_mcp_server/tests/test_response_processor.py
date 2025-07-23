"""
Tests for the response processor module.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from fixed_schema_mcp_server.response.response_processor import ResponseProcessor
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError
from fixed_schema_mcp_server.response.exceptions import ResponseProcessingError


class TestResponseProcessor:
    """Test cases for the ResponseProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock schema manager
        self.mock_schema_manager = MagicMock()
        
        # Create a test schema
        self.test_schema = {
            "type": "object",
            "required": ["name", "age", "email"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string", "format": "email"}
            }
        }
        
        # Configure the mock schema manager
        self.mock_schema_manager.get_schema.return_value = MagicMock(schema=self.test_schema)
        self.mock_schema_manager.validate_against_schema.return_value = True
        
        # Create the response processor
        self.response_processor = ResponseProcessor(self.mock_schema_manager)
    
    @pytest.mark.asyncio
    async def test_process_response_valid_json(self):
        """Test processing a valid JSON response."""
        # Create a valid JSON response
        raw_response = '{"name": "John Doe", "age": 30, "email": "john@example.com"}'
        
        # Process the response
        result = await self.response_processor.process_response(raw_response, "test_schema")
        
        # Verify the result
        assert result == json.loads(raw_response)
        self.mock_schema_manager.validate_against_schema.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_response_json_in_markdown(self):
        """Test processing a JSON response embedded in markdown."""
        # Create a markdown response with embedded JSON
        raw_response = """
        Here's the information you requested:
        
        ```json
        {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        ```
        
        Let me know if you need anything else.
        """
        
        # Process the response
        result = await self.response_processor.process_response(raw_response, "test_schema")
        
        # Verify the result
        expected = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        assert result == expected
        self.mock_schema_manager.validate_against_schema.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_response_invalid_json(self):
        """Test processing an invalid JSON response."""
        # Create an invalid JSON response
        raw_response = 'This is not valid JSON'
        
        # Configure the mock to extract JSON from text
        with patch.object(self.response_processor, '_extract_json', side_effect=json.JSONDecodeError('Invalid JSON', raw_response, 0)):
            # Process the response should raise an exception
            with pytest.raises(Exception):
                await self.response_processor.process_response(raw_response, "test_schema")
    
    @pytest.mark.asyncio
    async def test_process_response_invalid_schema(self):
        """Test processing a response that doesn't match the schema."""
        # Create a JSON response missing required fields
        raw_response = '{"name": "John Doe", "age": 30}'  # Missing email
        
        # Configure the mock to fail validation
        self.mock_schema_manager.validate_against_schema.return_value = False
        
        # Configure the mock to return validation errors
        validation_result = MagicMock()
        validation_result.valid = False
        validation_result.errors = [
            MagicMock(path="email", message="Required field missing", value="None")
        ]
        self.mock_schema_manager.validate_with_details.return_value = validation_result
        
        # Configure the fix_response method to add the missing field
        fixed_response = json.loads(raw_response)
        fixed_response["email"] = "john@example.com"
        with patch.object(self.response_processor, 'fix_response', return_value=fixed_response):
            # Process the response
            result = await self.response_processor.process_response(raw_response, "test_schema")
            
            # Verify the result
            assert "email" in result
            assert result["email"] == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_process_response_schema_not_found(self):
        """Test processing a response with a non-existent schema."""
        # Configure the mock to raise SchemaNotFoundError
        self.mock_schema_manager.get_schema.side_effect = SchemaNotFoundError("Schema not found")
        
        # Process the response should raise SchemaNotFoundError
        with pytest.raises(SchemaNotFoundError):
            await self.response_processor.process_response('{"name": "John"}', "nonexistent_schema")
    
    def test_validate_response_valid(self):
        """Test validating a valid response."""
        # Create a valid response
        response = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        
        # Configure the mock to return True for validation
        self.mock_schema_manager.validate_against_schema.return_value = True
        
        # Validate the response
        result = self.response_processor.validate_response(response, "test_schema")
        
        # Verify the result
        assert result is True
        self.mock_schema_manager.validate_against_schema.assert_called_once_with(response, "test_schema")
    
    def test_validate_response_invalid(self):
        """Test validating an invalid response."""
        # Create an invalid response
        response = {
            "name": "John Doe",
            "age": -5,  # Invalid age
            "email": "not-an-email"  # Invalid email
        }
        
        # Configure the mock to return False for validation
        self.mock_schema_manager.validate_against_schema.return_value = False
        
        # Validate the response
        result = self.response_processor.validate_response(response, "test_schema")
        
        # Verify the result
        assert result is False
        self.mock_schema_manager.validate_against_schema.assert_called_once_with(response, "test_schema")
    
    def test_validate_response_schema_not_found(self):
        """Test validating a response with a non-existent schema."""
        # Configure the mock to raise SchemaNotFoundError
        self.mock_schema_manager.validate_against_schema.side_effect = SchemaNotFoundError("Schema not found")
        
        # Validate the response should raise SchemaNotFoundError
        with pytest.raises(SchemaNotFoundError):
            self.response_processor.validate_response({}, "nonexistent_schema")
    
    def test_fix_response_missing_required(self):
        """Test fixing a response with missing required fields."""
        # Create a response with missing required fields
        response = {
            "name": "John Doe",
            "age": 30
            # Missing email
        }
        
        # Configure the mock schema
        schema_model = MagicMock()
        schema_model.schema = MagicMock()
        schema_model.schema.model_dump.return_value = self.test_schema
        self.mock_schema_manager.get_schema.return_value = schema_model
        
        # Configure validation result
        validation_result = MagicMock()
        validation_result.valid = False
        validation_result.errors = [
            MagicMock(path="email", message="Required field missing", value="None")
        ]
        self.mock_schema_manager.validate_with_details.return_value = validation_result
        
        # Fix the response
        fixed_response = self.response_processor.fix_response(response, "test_schema")
        
        # Verify the result
        assert "email" in fixed_response
        assert isinstance(fixed_response["email"], str)
    
    def test_fix_response_wrong_types(self):
        """Test fixing a response with wrong field types."""
        # Create a response with wrong field types
        response = {
            "name": "John Doe",
            "age": "thirty",  # Should be an integer
            "email": 12345  # Should be a string
        }
        
        # Configure the mock schema
        schema_model = MagicMock()
        schema_model.schema = MagicMock()
        schema_model.schema.model_dump.return_value = self.test_schema
        self.mock_schema_manager.get_schema.return_value = schema_model
        
        # Configure validation result
        validation_result = MagicMock()
        validation_result.valid = False
        validation_result.errors = [
            MagicMock(path="age", message="Not an integer", value="thirty"),
            MagicMock(path="email", message="Not a string", value="12345")
        ]
        self.mock_schema_manager.validate_with_details.return_value = validation_result
        
        # Fix the response
        fixed_response = self.response_processor.fix_response(response, "test_schema")
        
        # Verify the result
        assert isinstance(fixed_response["age"], int)
        assert isinstance(fixed_response["email"], str)
    
    def test_extract_json_valid(self):
        """Test extracting JSON from a valid JSON string."""
        # Create a valid JSON string
        json_str = '{"name": "John Doe", "age": 30, "email": "john@example.com"}'
        
        # Extract the JSON
        result = self.response_processor._extract_json(json_str)
        
        # Verify the result
        expected = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        assert result == expected
    
    def test_extract_json_from_markdown(self):
        """Test extracting JSON from a markdown code block."""
        # Create a markdown string with a JSON code block
        markdown_str = """
        Here's the information you requested:
        
        ```json
        {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        ```
        
        Let me know if you need anything else.
        """
        
        # Extract the JSON
        result = self.response_processor._extract_json(markdown_str)
        
        # Verify the result
        expected = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        assert result == expected
    
    def test_extract_json_from_text(self):
        """Test extracting JSON from text with a JSON object."""
        # Create a text string with a JSON object
        text_str = """
        Here's the information:
        
        {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        
        Let me know if you need anything else.
        """
        
        # Extract the JSON
        result = self.response_processor._extract_json(text_str)
        
        # Verify the result
        expected = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        assert result == expected
    
    def test_extract_json_invalid(self):
        """Test extracting JSON from an invalid string."""
        # Create an invalid string
        invalid_str = "This is not valid JSON"
        
        # Extract the JSON should raise an exception
        with pytest.raises(json.JSONDecodeError):
            self.response_processor._extract_json(invalid_str)