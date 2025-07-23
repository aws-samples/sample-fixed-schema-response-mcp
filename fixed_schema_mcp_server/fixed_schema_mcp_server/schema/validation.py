"""
Schema validation functionality for the Fixed Schema Response MCP Server.

This module provides functionality for validating data against JSON schemas.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional, Union

import jsonschema
from jsonschema.exceptions import ValidationError

from fixed_schema_mcp_server.schema.exceptions import SchemaValidationError

logger = logging.getLogger(__name__)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.
    
    Args:
        data: The data to validate
        schema: The JSON schema to validate against
        
    Returns:
        True if the data is valid, False otherwise
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True
    except ValidationError:
        return False

def validate_with_detailed_errors(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
    """
    Validate data against a JSON schema and return detailed errors.
    
    Args:
        data: The data to validate
        schema: The JSON schema to validate against
        
    Returns:
        A tuple of (is_valid, errors)
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        # Extract validation errors
        errors = []
        for error in sorted(e.context, key=lambda e: e.schema_path):
            errors.append(f"{'.'.join(str(p) for p in error.absolute_path)}: {error.message}")
        
        return False, errors