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
#     "openai>=1.0.0",
#     "anthropic>=0.25.0",
# ]
# requires-python = ">=3.10"
# ///

import json
import logging
import os
import boto3
import time
import re
from typing import Any, Dict, List, Callable, Optional
from functools import partial

from mcp.server.fastmcp import FastMCP
from security_config import SecurityValidator, get_secure_config_defaults

# Security constants
MAX_SCHEMA_NAME_LENGTH = 50
MAX_SYSTEM_PROMPT_LENGTH = 2000
VALID_SCHEMA_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
DEFAULT_MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("generic-schema")

# Global variables for model clients
bedrock_runtime = None
openai_client = None
anthropic_client = None

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

def initialize_model_clients(config: Dict[str, Any]) -> None:
    """
    Initialize model clients based on configuration and environment variables.
    Supports credentials from config file and environment variables (set via MCP config).
    
    Args:
        config: Configuration dictionary
    """
    global bedrock_runtime, openai_client, anthropic_client
    
    model_config = config.get("model", {})
    provider = model_config.get("provider", "mock")
    
    # Initialize all providers to check for available credentials
    # This allows switching providers without restarting the server
    
    # AWS Bedrock initialization
    try:
        credentials = model_config.get("credentials", {})
        
        # Get AWS region (config -> env -> default)
        aws_region = (
            credentials.get("aws_region") or 
            os.getenv("AWS_REGION") or 
            os.getenv("AWS_DEFAULT_REGION") or 
            "us-west-2"
        )
        
        # Initialize AWS session with credentials
        session_kwargs = {"region_name": aws_region}
        
        # Priority: config file -> environment variables -> AWS profile
        profile_name = credentials.get("profile_name") or os.getenv("AWS_PROFILE")
        if profile_name:
            session_kwargs["profile_name"] = profile_name
            logger.info(f"Using AWS profile: {profile_name}")
        
        # Use explicit credentials if provided (config or env)
        aws_access_key = (
            credentials.get("aws_access_key_id") or 
            os.getenv("AWS_ACCESS_KEY_ID")
        )
        aws_secret_key = (
            credentials.get("aws_secret_access_key") or 
            os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        aws_session_token = (
            credentials.get("aws_session_token") or 
            os.getenv("AWS_SESSION_TOKEN")
        )
        
        if aws_access_key and aws_secret_key:
            session_kwargs.update({
                "aws_access_key_id": aws_access_key,
                "aws_secret_access_key": aws_secret_key
            })
            if aws_session_token:
                session_kwargs["aws_session_token"] = aws_session_token
            logger.info("Using explicit AWS credentials")
        
        session = boto3.Session(**session_kwargs)
        bedrock_runtime = session.client('bedrock-runtime')
        logger.info(f"Successfully initialized AWS Bedrock client in region {aws_region}")
        
    except Exception as e:
        logger.error(f"Failed to initialize AWS Bedrock client: {e}")
        logger.info("AWS Bedrock unavailable - will use mock responses if selected")
        bedrock_runtime = None
    
    # OpenAI initialization
    try:
        openai_config = model_config.get("openai", {})
        api_key = (
            openai_config.get("api_key") or 
            os.getenv("OPENAI_API_KEY")
        )
        
        if api_key:
            # Import OpenAI client
            try:
                from openai import OpenAI
                openai_client = OpenAI(
                    api_key=api_key,
                    base_url=openai_config.get("base_url") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    organization=openai_config.get("organization") or os.getenv("OPENAI_ORGANIZATION")
                )
                logger.info("Successfully initialized OpenAI client")
            except ImportError:
                logger.error("OpenAI package not installed. Install with: uv add openai")
        else:
            logger.info("OpenAI API key not found - set OPENAI_API_KEY environment variable in MCP config")
                
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        openai_client = None
    
    # Anthropic initialization
    try:
        anthropic_config = model_config.get("anthropic", {})
        api_key = (
            anthropic_config.get("api_key") or 
            os.getenv("ANTHROPIC_API_KEY")
        )
        
        if api_key:
            # Import Anthropic client
            try:
                from anthropic import Anthropic
                anthropic_client = Anthropic(api_key=api_key)
                logger.info("Successfully initialized Anthropic client")
            except ImportError:
                logger.error("Anthropic package not installed. Install with: uv add anthropic")
        else:
            logger.info("Anthropic API key not found - set ANTHROPIC_API_KEY environment variable in MCP config")
                
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}")
        anthropic_client = None
    
    # Log current provider
    logger.info(f"Current provider: {provider}")
    if provider == "aws_bedrock" and bedrock_runtime is None:
        logger.warning("AWS Bedrock selected but not available - will use mock responses")
    elif provider == "openai" and openai_client is None:
        logger.warning("OpenAI selected but not available - will use mock responses")
    elif provider == "anthropic" and anthropic_client is None:
        logger.warning("Anthropic selected but not available - will use mock responses")
    elif provider == "mock":
        logger.info("Using mock provider - no client initialization needed")

# Initialize model clients
initialize_model_clients(CONFIG)

# Log schema loading results
if not SCHEMAS:
    logger.warning("No schemas found! Server will start but no schema tools will be available.")
    logger.info("You can add schemas dynamically using the 'add_schema' tool.")
else:
    logger.info(f"Successfully loaded {len(SCHEMAS)} schemas from files: {list(SCHEMAS.keys())}")

def invoke_model(prompt: str, schema_name: str) -> Dict[str, Any]:
    """
    Invoke the configured model to generate a response based on the prompt and schema.
    
    Args:
        prompt: The prompt to send to the model
        schema_name: The name of the schema to use for validation
        
    Returns:
        The parsed JSON response from the model
    """
    model_config = CONFIG.get("model", {})
    provider = model_config.get("provider", "mock")
    model_id = model_config.get("model_id", "")
    parameters = model_config.get("parameters", {})
    
    logger.info(f"=== INVOKING MODEL ===")
    logger.info(f"Provider: {provider}")
    logger.info(f"Model ID: {model_id}")
    logger.info(f"Schema name: {schema_name}")
    
    # Route to appropriate provider
    if provider == "aws_bedrock":
        return invoke_aws_bedrock(prompt, schema_name, model_id, parameters)
    elif provider == "openai":
        return invoke_openai(prompt, schema_name, model_id, parameters)
    elif provider == "anthropic":
        return invoke_anthropic(prompt, schema_name, model_id, parameters)
    else:
        logger.info(f"Using mock provider for {provider}")
        return generate_mock_response(prompt, schema_name)

def invoke_aws_bedrock(prompt: str, schema_name: str, model_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke AWS Bedrock model."""
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

        # Prepare the request based on model type
        if "anthropic.claude" in model_id or "us.anthropic.claude" in model_id:
            request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": parameters.get("max_tokens", 4096),
                "temperature": parameters.get("temperature", 0.2),
                "top_p": parameters.get("top_p", 0.9),
                "system": system_message,
                "messages": [{"role": "user", "content": prompt}]
            }
        elif "amazon.titan" in model_id:
            request = {
                "inputText": f"{system_message}\n\nUser: {prompt}",
                "textGenerationConfig": {
                    "maxTokenCount": parameters.get("max_tokens", 4096),
                    "temperature": parameters.get("temperature", 0.2),
                    "topP": parameters.get("top_p", 0.9)
                }
            }
        else:
            logger.warning(f"Unknown Bedrock model type: {model_id}")
            return generate_mock_response(prompt, schema_name)
        
        logger.info(f"Attempting to invoke Bedrock model: {model_id}")
        logger.info(f"Request payload size: {len(json.dumps(request))} characters")
        
        start_time = time.time()
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request)
        )
        end_time = time.time()
        
        logger.info(f"Bedrock API call successful in {end_time - start_time:.2f} seconds")
        
        # Parse response based on model type
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        if "anthropic.claude" in model_id or "us.anthropic.claude" in model_id:
            content = response_body['content'][0]['text']
        elif "amazon.titan" in model_id:
            content = response_body['results'][0]['outputText']
        else:
            content = str(response_body)
        
        return extract_json_from_response(content, prompt, schema_name)
            
    except Exception as e:
        logger.error(f"Error invoking Claude: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return generate_mock_response(prompt, schema_name)

def invoke_openai(prompt: str, schema_name: str, model_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke OpenAI model."""
    if openai_client is None:
        logger.warning("OpenAI client not available, using mock response")
        return generate_mock_response(prompt, schema_name)
    
    try:
        # Get the schema and system prompt
        schema_config = SCHEMAS.get(schema_name, {})
        schema = schema_config.get("schema", {})
        custom_system_prompt = schema_config.get("system_prompt", "")
        schema_json = json.dumps(schema, indent=2)
        
        # Create the system message
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

        start_time = time.time()
        response = openai_client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=parameters.get("temperature", 0.2),
            top_p=parameters.get("top_p", 0.9),
            max_tokens=parameters.get("max_tokens", 4096)
        )
        end_time = time.time()
        
        logger.info(f"OpenAI API call successful in {end_time - start_time:.2f} seconds")
        
        content = response.choices[0].message.content
        return extract_json_from_response(content, prompt, schema_name)
        
    except Exception as e:
        logger.error(f"Error invoking OpenAI: {e}")
        return generate_mock_response(prompt, schema_name)

def invoke_anthropic(prompt: str, schema_name: str, model_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke Anthropic model."""
    if anthropic_client is None:
        logger.warning("Anthropic client not available, using mock response")
        return generate_mock_response(prompt, schema_name)
    
    try:
        # Get the schema and system prompt
        schema_config = SCHEMAS.get(schema_name, {})
        schema = schema_config.get("schema", {})
        custom_system_prompt = schema_config.get("system_prompt", "")
        schema_json = json.dumps(schema, indent=2)
        
        # Create the system message
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

        start_time = time.time()
        response = anthropic_client.messages.create(
            model=model_id,
            system=system_message,
            messages=[{"role": "user", "content": prompt}],
            temperature=parameters.get("temperature", 0.2),
            top_p=parameters.get("top_p", 0.9),
            max_tokens=parameters.get("max_tokens", 4096)
        )
        end_time = time.time()
        
        logger.info(f"Anthropic API call successful in {end_time - start_time:.2f} seconds")
        
        content = response.content[0].text
        return extract_json_from_response(content, prompt, schema_name)
        
    except Exception as e:
        logger.error(f"Error invoking Anthropic: {e}")
        return generate_mock_response(prompt, schema_name)

def extract_json_from_response(content: str, prompt: str, schema_name: str) -> Dict[str, Any]:
    """Extract JSON from model response."""
    logger.info(f"Model response length: {len(content)} characters")
    
    try:
        # Look for JSON content
        if content.strip().startswith('{') and content.strip().endswith('}'):
            result = json.loads(content)
        else:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # Try to find JSON within the response
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    logger.warning("Failed to extract JSON from model response, using mock response")
                    return generate_mock_response(prompt, schema_name)
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse model response as JSON: {e}")
        logger.error(f"Raw response: {content}")
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
        
        return invoke_model(prompt, schema_name)
    
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
    Add a new schema by creating a persistent schema file.
    
    This tool creates a schema file in the test_config/schemas directory.
    The server must be restarted for the new schema to become available as a tool.
    
    Args:
        schema_name: Name for the new schema
        schema_definition: JSON schema definition as a string
        description: Optional description of the schema
        system_prompt: Optional custom system prompt for this schema
        
    Returns:
        Status of the schema addition
    """
    logger.info(f"Creating schema file for: {schema_name}")
    
    try:
        # Validate schema name using security validator
        is_valid, error_msg = SecurityValidator.validate_schema_name(schema_name)
        if not is_valid:
            return {
                "status": "error",
                "message": error_msg
            }
        
        # Validate JSON schema definition
        is_valid, error_msg, schema_json = SecurityValidator.validate_json_schema(schema_definition)
        if not is_valid:
            return {
                "status": "error",
                "message": error_msg
            }
        
        # Create schema config
        schema_config = {
            "name": schema_name,
            "description": description or f"Schema for {schema_name}",
            "schema": schema_json
        }
        
        if system_prompt:
            # Validate system prompt using security validator
            is_valid, error_msg = SecurityValidator.validate_system_prompt(system_prompt)
            if not is_valid:
                return {
                    "status": "error",
                    "message": error_msg
                }
            schema_config["system_prompt"] = system_prompt
        
        # Get the schemas directory path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schemas_dir = os.path.join(script_dir, "test_config", "schemas")
        
        # Ensure the schemas directory exists
        os.makedirs(schemas_dir, exist_ok=True)
        
        # Validate the final path to prevent directory traversal
        schema_file_path = os.path.join(schemas_dir, f"{schema_name}.json")
        is_valid, error_msg = SecurityValidator.validate_file_path(schema_file_path, schemas_dir)
        if not is_valid:
            return {
                "status": "error",
                "message": f"Invalid file path: {error_msg}"
            }
        
        # Check if file already exists
        if os.path.exists(schema_file_path):
            return {
                "status": "error",
                "message": f"Schema '{schema_name}' already exists. Use a different name."
            }
        
        # Write the schema file with proper error handling
        try:
            with open(schema_file_path, 'w', encoding='utf-8') as f:
                json.dump(schema_config, f, indent=2, ensure_ascii=False)
        except OSError as e:
            return {
                "status": "error",
                "message": f"Failed to write schema file: {str(e)}"
            }
        
        logger.info(f"Successfully created schema file: {schema_file_path}")
        
        return {
            "status": "success",
            "message": f"Schema '{schema_name}' file created successfully. Restart the MCP server to make the 'get_{schema_name}' tool available.",
            "tool_name": f"get_{schema_name}",
            "schema_name": schema_name,
            "file_path": schema_file_path,
            "restart_required": True
        }
        
    except Exception as e:
        error_msg = f"Unexpected error creating schema file: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
def get_model_config() -> Dict[str, Any]:
    """
    Get the current model configuration including provider, model ID, and available options.
    
    Returns:
        Current model configuration and available providers/models
    """
    logger.info("Getting model configuration")
    
    model_config = CONFIG.get("model", {})
    return {
        "current_config": {
            "provider": model_config.get("provider", "mock"),
            "model_id": model_config.get("model_id", ""),
            "parameters": model_config.get("parameters", {}),
            "credentials_configured": {
                "aws_bedrock": bedrock_runtime is not None,
                "openai": openai_client is not None,
                "anthropic": anthropic_client is not None
            }
        },
        "available_providers": model_config.get("available_providers", {}),
        "config_file_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_config", "config.json")
    }

@mcp.tool()
def update_model_config(provider: str, model_id: str, temperature: float = 0.2, max_tokens: int = 4096, top_p: float = 0.9) -> Dict[str, Any]:
    """
    Update the model configuration. Server restart required for changes to take effect.
    
    Args:
        provider: Model provider (aws_bedrock, openai, anthropic, mock)
        model_id: Specific model ID to use
        temperature: Temperature parameter (0.0-1.0)
        max_tokens: Maximum tokens to generate
        top_p: Top-p parameter (0.0-1.0)
        
    Returns:
        Status of the configuration update
    """
    logger.info(f"Updating model configuration: {provider} / {model_id}")
    
    try:
        # Load current config
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "test_config", "config.json")
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Update model configuration
        config["model"]["provider"] = provider
        config["model"]["model_id"] = model_id
        config["model"]["parameters"]["temperature"] = temperature
        config["model"]["parameters"]["max_tokens"] = max_tokens
        config["model"]["parameters"]["top_p"] = top_p
        
        # Write updated config
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Successfully updated model configuration")
        
        return {
            "status": "success",
            "message": f"Model configuration updated to use {provider} with {model_id}. Restart the MCP server for changes to take effect.",
            "updated_config": {
                "provider": provider,
                "model_id": model_id,
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p
                }
            },
            "restart_required": True
        }
        
    except Exception as e:
        error_msg = f"Failed to update model configuration: {e}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
def update_credentials(provider: str, **credentials) -> Dict[str, Any]:
    """
    Update credentials for a specific provider. Server restart required for changes to take effect.
    
    Args:
        provider: Provider to update credentials for (aws_bedrock, openai, anthropic)
        **credentials: Provider-specific credential parameters
        
    For AWS Bedrock:
        - aws_region: AWS region (default: us-west-2)
        - aws_access_key_id: AWS access key ID
        - aws_secret_access_key: AWS secret access key
        - aws_session_token: AWS session token (optional)
        - profile_name: AWS profile name (optional)
        
    For OpenAI:
        - api_key: OpenAI API key
        - base_url: API base URL (optional)
        - organization: Organization ID (optional)
        
    For Anthropic:
        - api_key: Anthropic API key
        
    Returns:
        Status of the credential update
    """
    logger.info(f"Updating credentials for provider: {provider}")
    
    try:
        # Load current config
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "test_config", "config.json")
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Update credentials based on provider
        if provider == "aws_bedrock":
            creds = config["model"].setdefault("credentials", {})
            if "aws_region" in credentials:
                creds["aws_region"] = credentials["aws_region"]
            if "aws_access_key_id" in credentials:
                creds["aws_access_key_id"] = credentials["aws_access_key_id"]
            if "aws_secret_access_key" in credentials:
                creds["aws_secret_access_key"] = credentials["aws_secret_access_key"]
            if "aws_session_token" in credentials:
                creds["aws_session_token"] = credentials["aws_session_token"]
            if "profile_name" in credentials:
                creds["profile_name"] = credentials["profile_name"]
                
        elif provider == "openai":
            openai_config = config["model"].setdefault("openai", {})
            if "api_key" in credentials:
                openai_config["api_key"] = credentials["api_key"]
            if "base_url" in credentials:
                openai_config["base_url"] = credentials["base_url"]
            if "organization" in credentials:
                openai_config["organization"] = credentials["organization"]
                
        elif provider == "anthropic":
            anthropic_config = config["model"].setdefault("anthropic", {})
            if "api_key" in credentials:
                anthropic_config["api_key"] = credentials["api_key"]
        else:
            return {
                "status": "error",
                "message": f"Unknown provider: {provider}. Supported providers: aws_bedrock, openai, anthropic"
            }
        
        # Write updated config
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Successfully updated credentials for {provider}")
        
        return {
            "status": "success",
            "message": f"Credentials updated for {provider}. Restart the MCP server for changes to take effect.",
            "provider": provider,
            "restart_required": True
        }
        
    except Exception as e:
        error_msg = f"Failed to update credentials: {e}"
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