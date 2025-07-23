#!/usr/bin/env python3
"""
Test script to load schemas directly.
"""

import json
import os
import sys
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class SchemaDefinition(BaseModel):
    """Schema definition model."""
    
    name: str = Field(..., description="The name of the schema")
    description: str = Field(..., description="A description of the schema")
    schema: Dict[str, Any] = Field(..., description="The JSON schema definition")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to use with this schema")

def main():
    """Main function."""
    # Get the schema path from the command line
    if len(sys.argv) > 1:
        schema_path = sys.argv[1]
    else:
        schema_path = "fixed_schema_mcp_server/test_config/schemas"
    
    # Get the absolute path
    abs_path = os.path.abspath(schema_path)
    print(f"Loading schemas from absolute path: {abs_path}")
    
    # Check if the directory exists and is readable
    if not os.path.isdir(abs_path):
        print(f"Schema path is not a directory: {abs_path}")
        return
    
    if not os.access(abs_path, os.R_OK):
        print(f"Schema path is not readable: {abs_path}")
        return
    
    # List all files in the directory
    try:
        files = os.listdir(abs_path)
        print(f"Found {len(files)} files in schema directory: {files}")
    except Exception as e:
        print(f"Error listing schema directory: {e}")
        return
    
    # Load all schema files
    schemas = {}
    for filename in files:
        if filename.endswith(".json"):
            file_path = os.path.join(abs_path, filename)
            try:
                print(f"Loading schema from {file_path}")
                with open(file_path, "r") as f:
                    schema_data = json.load(f)
                
                # Print the schema data
                print(f"Schema data: {json.dumps(schema_data)}")
                
                # Create a schema definition
                schema = SchemaDefinition(**schema_data)
                
                # Add the schema to the dictionary
                schemas[schema.name] = schema
                
                print(f"Loaded schema '{schema.name}' from {file_path}")
                
            except Exception as e:
                print(f"Error loading schema from {file_path}: {e}")
    
    # Print all loaded schemas
    print(f"Loaded {len(schemas)} schemas: {list(schemas.keys())}")

if __name__ == "__main__":
    main()