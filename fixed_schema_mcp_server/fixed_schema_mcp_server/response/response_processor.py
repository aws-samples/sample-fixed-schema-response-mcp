"""
Response processing functionality for the Fixed Schema Response MCP Server.

This module provides functionality for processing raw model responses,
formatting them according to schemas, and validating the final responses.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List, Union

from fixed_schema_mcp_server.core.interfaces import ResponseProcessorInterface
from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError, SchemaValidationError

logger = logging.getLogger(__name__)

class ResponseProcessor(ResponseProcessorInterface):
    """
    Response processor for the Fixed Schema Response MCP Server.
    
    This class is responsible for processing raw model responses,
    formatting them according to schemas, and validating the final responses.
    """
    
    def __init__(self, schema_manager):
        """
        Initialize the response processor.
        
        Args:
            schema_manager: The schema manager to use for schema operations
        """
        self._schema_manager = schema_manager
    
    async def process_response(self, raw_response: str, schema_name: str) -> Dict[str, Any]:
        """
        Process and format the raw response according to the schema.
        
        Args:
            raw_response: The raw response from the model
            schema_name: The name of the schema to format against
            
        Returns:
            The processed response as a dictionary
            
        Raises:
            SchemaNotFoundError: If the schema does not exist
            SchemaValidationError: If the response cannot be formatted according to the schema
        """
        try:
            # Extract JSON from the response
            json_data = self._extract_json(raw_response)
            
            # Validate the response against the schema
            if not self.validate_response(json_data, schema_name):
                # Try to fix the response
                json_data = self.fix_response(json_data, schema_name)
                
                # Validate again
                if not self.validate_response(json_data, schema_name):
                    raise SchemaValidationError("Response does not conform to schema")
            
            return json_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            raise SchemaValidationError(f"Error parsing JSON response: {e}")
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            raise SchemaValidationError(f"Error processing response: {e}")
    
    def validate_response(self, processed_response: Dict[str, Any], schema_name: str) -> bool:
        """
        Validate the processed response against the schema.
        
        Args:
            processed_response: The processed response to validate
            schema_name: The name of the schema to validate against
            
        Returns:
            True if the response is valid, False otherwise
            
        Raises:
            SchemaNotFoundError: If the schema does not exist
        """
        return self._schema_manager.validate_against_schema(processed_response, schema_name)
    
    def fix_response(self, response: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """
        Attempt to fix a response that doesn't conform to the schema.
        
        Args:
            response: The response to fix
            schema_name: The name of the schema to fix against
            
        Returns:
            The fixed response as a dictionary
            
        Raises:
            SchemaNotFoundError: If the schema does not exist
        """
        # Get the schema
        schema = self._schema_manager.get_schema(schema_name)
        
        # Get the required fields
        required_fields = schema.schema.get("required", [])
        
        # Get the properties
        properties = schema.schema.get("properties", {})
        
        # Check for missing required fields
        for field in required_fields:
            if field not in response:
                # Add a default value based on the field type
                field_type = properties.get(field, {}).get("type")
                
                if field_type == "string":
                    response[field] = ""
                elif field_type == "number":
                    response[field] = 0
                elif field_type == "integer":
                    response[field] = 0
                elif field_type == "boolean":
                    response[field] = False
                elif field_type == "array":
                    response[field] = []
                elif field_type == "object":
                    response[field] = {}
        
        # Check for fields with incorrect types
        for field, value in list(response.items()):
            if field in properties:
                field_type = properties[field].get("type")
                
                # Fix type mismatches
                if field_type == "string" and not isinstance(value, str):
                    response[field] = str(value)
                elif field_type == "number" and not isinstance(value, (int, float)):
                    try:
                        response[field] = float(value)
                    except (ValueError, TypeError):
                        response[field] = 0
                elif field_type == "integer" and not isinstance(value, int):
                    try:
                        response[field] = int(value)
                    except (ValueError, TypeError):
                        response[field] = 0
                elif field_type == "boolean" and not isinstance(value, bool):
                    response[field] = bool(value)
                elif field_type == "array" and not isinstance(value, list):
                    response[field] = []
                elif field_type == "object" and not isinstance(value, dict):
                    response[field] = {}
        
        return response
    
    def _extract_json(self, raw_response: str) -> Dict[str, Any]:
        """
        Extract JSON from a raw response.
        
        Args:
            raw_response: The raw response from the model
            
        Returns:
            The extracted JSON as a dictionary
            
        Raises:
            json.JSONDecodeError: If the response cannot be parsed as JSON
        """
        # Log the raw response for debugging
        logger.debug(f"Raw response to extract JSON from: {raw_response}")
        
        # Try to parse the entire response as JSON
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse entire response as JSON: {e}")
        
        # Try to extract JSON from the response using regex for code blocks
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        matches = re.findall(json_pattern, raw_response)
        
        if matches:
            # Try each match
            for match in matches:
                try:
                    logger.debug(f"Trying to parse JSON from code block: {match}")
                    return json.loads(match)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON from code block: {e}")
                    continue
        
        # Try to find JSON between curly braces
        json_pattern = r'({[\s\S]*?})'
        matches = re.findall(json_pattern, raw_response)
        
        if matches:
            # Try each match
            for match in matches:
                try:
                    logger.debug(f"Trying to parse JSON between curly braces: {match}")
                    return json.loads(match)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON between curly braces: {e}")
                    continue
        
        # If the response is empty or whitespace, return an empty object
        if not raw_response or raw_response.isspace():
            logger.warning("Empty or whitespace response, returning empty object")
            return {}
        
        # If all else fails, try to create a simple JSON object with the response as a message
        try:
            logger.warning("Could not extract JSON, creating a simple JSON object with the response as a message")
            return {"message": raw_response}
        except Exception as e:
            logger.error(f"Failed to create simple JSON object: {e}")
            raise json.JSONDecodeError("Could not extract JSON from response", raw_response, 0)