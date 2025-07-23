"""
Schema management functionality for the Fixed Schema Response MCP Server.

This module provides functionality for loading, validating, and managing schemas.
"""

import json
import logging
import os
from typing import Dict, Any, List, Tuple, Optional, Union

import jsonschema
from pydantic import BaseModel, Field

from fixed_schema_mcp_server.schema.exceptions import SchemaNotFoundError, SchemaValidationError

logger = logging.getLogger(__name__)

class SchemaDefinition(BaseModel):
    """Schema definition model."""
    
    name: str = Field(..., description="The name of the schema")
    description: str = Field(..., description="A description of the schema")
    schema: Dict[str, Any] = Field(..., description="The JSON schema definition")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to use with this schema")

class SchemaManager:
    """
    Schema manager for the Fixed Schema Response MCP Server.
    
    This class is responsible for loading, validating, and managing schemas.
    """
    
    def __init__(self):
        """Initialize the schema manager."""
        self._schemas = {}
        self._schema_path = None
    
    def load_schemas(self, schema_path: str) -> None:
        """
        Load schemas from the specified path.
        
        Args:
            schema_path: Path to the schema definitions
            
        Raises:
            FileNotFoundError: If the schema path does not exist
            ValueError: If a schema file is invalid
        """
        if not os.path.exists(schema_path):
            logger.warning(f"Schema path '{schema_path}' does not exist, creating it")
            os.makedirs(schema_path, exist_ok=True)
        
        self._schema_path = schema_path
        self._schemas = {}
        
        # Log the absolute path
        abs_path = os.path.abspath(schema_path)
        logger.info(f"Loading schemas from absolute path: {abs_path}")
        
        # Check if the directory exists and is readable
        if not os.path.isdir(abs_path):
            logger.error(f"Schema path is not a directory: {abs_path}")
            raise ValueError(f"Schema path is not a directory: {abs_path}")
        
        if not os.access(abs_path, os.R_OK):
            logger.error(f"Schema path is not readable: {abs_path}")
            raise ValueError(f"Schema path is not readable: {abs_path}")
        
        # List all files in the directory
        try:
            files = os.listdir(abs_path)
            logger.info(f"Found {len(files)} files in schema directory: {files}")
        except Exception as e:
            logger.error(f"Error listing schema directory: {e}")
            raise ValueError(f"Error listing schema directory: {e}")
        
        # Load all schema files
        for filename in files:
            if filename.endswith(".json"):
                file_path = os.path.join(abs_path, filename)
                try:
                    logger.info(f"Loading schema from {file_path}")
                    with open(file_path, "r") as f:
                        schema_data = json.load(f)
                    
                    # Log the schema data
                    logger.debug(f"Schema data: {json.dumps(schema_data)}")
                    
                    # Create a schema definition
                    schema = SchemaDefinition(**schema_data)
                    
                    # Add the schema to the dictionary
                    self._schemas[schema.name] = schema
                    
                    logger.info(f"Loaded schema '{schema.name}' from {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error loading schema from {file_path}: {e}")
                    raise ValueError(f"Error loading schema from {file_path}: {e}")
        
        # Log all loaded schemas
        logger.info(f"Loaded {len(self._schemas)} schemas: {list(self._schemas.keys())}")
        logger.info(f"Loaded {len(self._schemas)} schemas from {schema_path}")
    
    def get_schema(self, schema_name: str) -> SchemaDefinition:
        """
        Get a schema by name.
        
        Args:
            schema_name: Name of the schema to retrieve
            
        Returns:
            The schema definition
            
        Raises:
            SchemaNotFoundError: If the schema does not exist
        """
        if schema_name not in self._schemas:
            raise SchemaNotFoundError(f"Schema not found: {schema_name}")
        
        return self._schemas[schema_name]
    
    def validate_against_schema(self, data: Dict[str, Any], schema_name: str) -> bool:
        """
        Validate data against a schema.
        
        Args:
            data: The data to validate
            schema_name: Name of the schema to validate against
            
        Returns:
            True if the data is valid, False otherwise
            
        Raises:
            SchemaNotFoundError: If the schema does not exist
        """
        schema = self.get_schema(schema_name)
        
        try:
            jsonschema.validate(instance=data, schema=schema.schema)
            return True
        except jsonschema.exceptions.ValidationError:
            return False
    
    def validate_with_detailed_errors(self, data: Dict[str, Any], schema_name: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate data against a schema and return detailed errors.
        
        Args:
            data: The data to validate
            schema_name: Name of the schema to validate against
            
        Returns:
            A tuple of (is_valid, errors)
            
        Raises:
            SchemaNotFoundError: If the schema does not exist
        """
        schema = self.get_schema(schema_name)
        
        try:
            jsonschema.validate(instance=data, schema=schema.schema)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            # Extract validation errors
            errors = []
            for error in sorted(e.context, key=lambda e: e.schema_path):
                errors.append(f"{'.'.join(str(p) for p in error.absolute_path)}: {error.message}")
            
            return False, errors
    
    def reload_schemas(self) -> None:
        """
        Reload schemas from disk.
        
        Raises:
            FileNotFoundError: If the schema path does not exist
            ValueError: If a schema file is invalid
        """
        if self._schema_path:
            self.load_schemas(self._schema_path)
    
    def get_all_schema_names(self) -> List[str]:
        """
        Get all schema names.
        
        Returns:
            A list of schema names
        """
        return list(self._schemas.keys())
    
    def get_schema_count(self) -> int:
        """
        Get the number of loaded schemas.
        
        Returns:
            The number of loaded schemas
        """
        return len(self._schemas)