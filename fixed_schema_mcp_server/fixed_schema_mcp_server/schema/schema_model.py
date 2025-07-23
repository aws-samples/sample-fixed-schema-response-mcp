"""
Schema data models for the Fixed Schema Response MCP Server.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SchemaDefinition(BaseModel):
    """
    Represents a JSON Schema definition.
    
    This is a wrapper around the raw JSON Schema dictionary that provides
    additional metadata and validation.
    """
    type: str = Field(..., description="The type of the schema (usually 'object')")
    required: Optional[List[str]] = Field(None, description="List of required properties")
    properties: Dict[str, Any] = Field(..., description="Schema properties definitions")
    additionalProperties: Optional[bool] = Field(True, description="Whether additional properties are allowed")
    
    class Config:
        extra = "allow"  # Allow additional fields in the schema


class Schema(BaseModel):
    """
    Represents a complete schema with metadata.
    
    This includes the actual JSON Schema definition along with additional
    metadata like name, description, and system prompt.
    """
    name: str = Field(..., description="The name of the schema")
    description: str = Field(..., description="A description of the schema")
    schema: SchemaDefinition = Field(..., description="The JSON Schema definition")
    system_prompt: Optional[str] = Field(None, description="System prompt to guide model responses")
    
    class Config:
        extra = "allow"  # Allow additional fields in the schema metadata