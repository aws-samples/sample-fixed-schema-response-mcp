#!/usr/bin/env python3
"""
Generic Schema MCP Server using FastMCP with AWS Bedrock Claude.

This module provides a FastMCP server implementation that dynamically loads JSON schemas
and creates corresponding tools for structured response generation using AWS Bedrock Claude.
"""
# /// script
# dependencies = [
#     "fastmcp>=0.1.0",
#     "boto3>=1.28.0",
#     "botocore>=1.31.0",
#     "jsonschema>=4.0.0",
# ]
# requires-python = ">=3.10"
# ///

import json
import logging
import os
import boto3
import time
from typing import Any, Dict, List, Callable
from functools import partial

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("generic-schema")

# Initialize AWS Bedrock client
try:
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-west-2'  # Change to your preferred region
    )
    logger.info("Successfully initialized AWS Bedrock client")
except Exception as e:
    logger.error(f"Failed to initialize AWS Bedrock client: {e}")
    logger.warning("Falling back to mock responses")
    bedrock_runtime = None

def load_schemas(schemas_dir: str = None) -> Dict[str, Dict[str, Any]]:
    """
    Load schemas from the specified directory or default test_config directory.
    
    Args:
        schemas_dir: Optional path to schemas directory. If None, uses default.
    
    Returns:
        A dictionary of schema name to schema definition
    """
    schemas = {}
    
    if schemas_dir is None:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schemas_dir = os.path.join(script_dir, "test_config", "schemas")
    
    # Check if the schemas directory exists
    if not os.path.exists(schemas_dir):
        logger.warning(f"Schemas directory not found: {schemas_dir}")
        return schemas
    
    # Load each schema file
    for filename in os.listdir(schemas_dir):
        if filename.endswith(".json"):
            schema_path = os.path.join(schemas_dir, filename)
            schema_name = os.path.splitext(filename)[0]
            
            try:
                with open(schema_path, "r") as f:
                    schema_data = json.load(f)
                schemas[schema_name] = schema_data
                logger.info(f"Loaded schema: {schema_name}")
            except Exception as e:
                logger.error(f"Failed to load schema {schema_name}: {e}")
    
    return schemas

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json file.
    
    Returns:
        Configuration dictionary
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "test_config", "config.json")
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logger.info("Loaded configuration from config.json")
        return config
    except Exception as e:
        logger.warning(f"Failed to load config.json: {e}")
        return {}

# Load configuration and schemas
CONFIG = load_config()
SCHEMAS_DIR = CONFIG.get("schemas", {}).get("path")
SCHEMAS = load_schemas(SCHEMAS_DIR)

# Log schema loading results
if not SCHEMAS:
    logger.warning("No schemas found! Server will start but no schema tools will be available.")
    logger.info("You can add schemas dynamically using the 'add_schema' tool.")
else:
    logger.info(f"Successfully loaded {len(SCHEMAS)} schemas from files: {list(SCHEMAS.keys())}")

def invoke_claude(prompt: str, schema_name: str) -> Dict[str, Any]:
    """
    Invoke Claude to generate a response based on the prompt and schema.
    
    Args:
        prompt: The prompt to send to Claude
        schema_name: The name of the schema to use for validation
        
    Returns:
        The parsed JSON response from Claude
    """
    logger.info(f"=== DEBUGGING invoke_claude ===")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Schema name: {schema_name}")
    logger.info(f"Bedrock client available: {bedrock_runtime is not None}")
    
    if bedrock_runtime is None:
        logger.warning("AWS Bedrock client not available, using mock response")
        return generate_mock_response(prompt, schema_name)
    
    try:
        # Get the schema and system prompt
        schema_config = SCHEMAS.get(schema_name, {})
        schema = schema_config.get("schema", {})
        custom_system_prompt = schema_config.get("system_prompt", "")
        schema_json = json.dumps(schema, indent=2)
        
        # Create the system message, using custom prompt if available
        if custom_system_prompt:
            system_message = f"""{custom_system_prompt}

Your response must strictly follow this JSON schema:

{schema_json}

Respond ONLY with valid JSON that matches this schema. Do not include any explanations, markdown formatting, or text outside the JSON structure."""
        else:
            system_message = f"""You are a helpful assistant that generates structured information in JSON format.
Please provide accurate and detailed information based on the user's query.
Your response must strictly follow this JSON schema:

{schema_json}

Respond ONLY with valid JSON that matches this schema. Do not include any explanations, markdown formatting, or text outside the JSON structure."""

        # Prepare the request
        request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.2,
            "system": system_message,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Invoke Claude
        logger.info(f"Attempting to invoke Claude with model: us.anthropic.claude-3-7-sonnet-20250219-v1:0")
        logger.info(f"Request payload size: {len(json.dumps(request))} characters")
        
        start_time = time.time()
        response = bedrock_runtime.invoke_model(
            modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            body=json.dumps(request)
        )
        end_time = time.time()
        
        logger.info(f"Claude API call successful in {end_time - start_time:.2f} seconds")
        
        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content = response_body['content'][0]['text']
        
        logger.info(f"Raw Claude response: {content[:500]}...")  # First 500 chars
        logger.info(f"Response starts with JSON: {content.strip().startswith('{')}")
        logger.info(f"Response ends with JSON: {content.strip().endswith('}')}")
        
        # Try to extract JSON from the response
        try:
            # Look for JSON content
            if content.strip().startswith('{') and content.strip().endswith('}'):
                result = json.loads(content)
            else:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Fall back to mock response
                    logger.warning("Failed to extract JSON from Claude response, using mock response")
                    return generate_mock_response(prompt, schema_name)
            
            logger.info(f"Claude response generated in {end_time - start_time:.2f} seconds")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Raw response: {content}")
            return generate_mock_response(prompt, schema_name)
            
    except Exception as e:
        logger.error(f"Error invoking Claude: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return generate_mock_response(prompt, schema_name)

def generate_mock_response(prompt: str, schema_name: str) -> Dict[str, Any]:
    """
    Generate a mock response based on the schema definition.
    
    Args:
        prompt: The prompt that would have been sent to Claude
        schema_name: The name of the schema to use
        
    Returns:
        A mock response that matches the schema
    """
    logger.info(f"Generating mock response for schema: {schema_name}")
    
    schema_config = SCHEMAS.get(schema_name)
    if not schema_config:
        return {"error": f"Unknown schema: {schema_name}"}
    
    schema = schema_config.get("schema", {})
    
    def generate_value_for_type(prop_schema: Dict[str, Any], field_name: str = "") -> Any:
        """Generate a mock value based on JSON schema type."""
        prop_type = prop_schema.get("type", "string")
        
        if prop_type == "string":
            if "email" in field_name.lower():
                return "example@example.com"
            elif "phone" in field_name.lower():
                return "555-123-4567"
            elif "date" in field_name.lower():
                return "2025-07-23"
            else:
                return f"Example {field_name}" if field_name else "Example value"
        
        elif prop_type == "integer":
            return 42
        
        elif prop_type == "number":
            return 99.99
        
        elif prop_type == "boolean":
            return True
        
        elif prop_type == "array":
            items_schema = prop_schema.get("items", {"type": "string"})
            return [generate_value_for_type(items_schema, f"{field_name}_item") for _ in range(2)]
        
        elif prop_type == "object":
            obj_properties = prop_schema.get("properties", {})
            result = {}
            for prop_name, prop_def in obj_properties.items():
                result[prop_name] = generate_value_for_type(prop_def, prop_name)
            return result
        
        else:
            return f"Mock value for {prop_type}"
    
    # Generate mock response based on schema
    try:
        properties = schema.get("properties", {})
        mock_response = {}
        
        for prop_name, prop_schema in properties.items():
            mock_response[prop_name] = generate_value_for_type(prop_schema, prop_name)
        
        return mock_response
        
    except Exception as e:
        logger.error(f"Error generating mock response: {e}")
        return {"error": f"Failed to generate mock response for schema: {schema_name}"}

def create_schema_tool(schema_name: str, schema_config: Dict[str, Any]) -> Callable:
    """
    Create a tool function for a given schema.
    
    Args:
        schema_name: Name of the schema
        schema_config: Schema configuration including description and schema definition
        
    Returns:
        A tool function that generates responses according to the schema
    """
    def schema_tool(query: str) -> Dict[str, Any]:
        """
        Generate structured response based on the schema.
        
        Args:
            query: The input query or request
            
        Returns:
            Structured response matching the schema
        """
        logger.info(f"Generating {schema_name} response for: {query}")
        
        # Use schema description to create a more specific prompt
        schema_description = schema_config.get("description", f"information about {schema_name}")
        prompt = f"Please provide {schema_description} based on this query: {query}"
        
        return invoke_claude(prompt, schema_name)
    
    # Set function metadata for MCP
    schema_tool.__name__ = f"get_{schema_name}"
    schema_tool.__doc__ = f"""
    {schema_config.get('description', f'Get {schema_name} information')}.
    
    Args:
        query: The input query or request
    
    Returns:
        {schema_name} information in a structured format
    """
    
    return schema_tool

def register_schema_tools():
    """
    Dynamically register tools for all loaded schemas.
    """
    for schema_name, schema_config in SCHEMAS.items():
        tool_func = create_schema_tool(schema_name, schema_config)
        
        # Register the tool with MCP
        mcp.tool()(tool_func)
        logger.info(f"Registered tool: get_{schema_name}")

# Register all schema tools
register_schema_tools()

# Add utility tools
@mcp.tool()
def list_available_schemas() -> Dict[str, Any]:
    """
    List all available schemas and their descriptions.
    
    Returns:
        Dictionary containing all available schemas and their descriptions
    """
    logger.info("Listing available schemas")
    
    schemas_info = {}
    for schema_name, schema_config in SCHEMAS.items():
        schemas_info[schema_name] = {
            "name": schema_name,
            "description": schema_config.get("description", "No description available"),
            "tool_name": f"get_{schema_name}"
        }
    
    return {
        "available_schemas": schemas_info,
        "total_count": len(schemas_info)
    }

@mcp.tool()
def add_schema(schema_name: str, schema_definition: str, description: str = "", system_prompt: str = "") -> Dict[str, Any]:
    """
    Add a new schema dynamically at runtime.
    
    Args:
        schema_name: Name for the new schema
        schema_definition: JSON schema definition as a string
        description: Optional description of the schema
        system_prompt: Optional custom system prompt for this schema
        
    Returns:
        Status of the schema addition
    """
    logger.info(f"Adding new schema: {schema_name}")
    
    try:
        # Parse the schema definition
        schema_json = json.loads(schema_definition)
        
        # Create schema config
        schema_config = {
            "name": schema_name,
            "description": description or f"Schema for {schema_name}",
            "schema": schema_json
        }
        
        if system_prompt:
            schema_config["system_prompt"] = system_prompt
        
        # Add to global schemas
        SCHEMAS[schema_name] = schema_config
        
        # Create and register the tool
        tool_func = create_schema_tool(schema_name, schema_config)
        mcp.tool()(tool_func)
        
        logger.info(f"Successfully added schema: {schema_name}")
        
        return {
            "status": "success",
            "message": f"Schema '{schema_name}' added successfully",
            "tool_name": f"get_{schema_name}",
            "schema_name": schema_name
        }
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON schema definition: {e}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Failed to add schema: {e}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

if __name__ == "__main__":
    # Initialize and run the server
    logger.info("Starting Generic Schema MCP Server using FastMCP with AWS Bedrock Claude")
    logger.info(f"Loaded {len(SCHEMAS)} schemas: {list(SCHEMAS.keys())}")
    
    if not SCHEMAS:
        logger.warning("No schemas loaded! Server will start but no schema tools will be available.")
        logger.info("You can add schemas dynamically using the 'add_schema' tool.")
    
    mcp.run(transport='stdio')