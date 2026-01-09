#!/usr/bin/env python3
"""
Schema Transform MCP Server using FastMCP.

This module provides a FastMCP server implementation that transforms unstructured text
into structured JSON using user-defined schemas. The server dynamically loads JSON schemas
and creates corresponding transform_to_{schema_name} tools for field extraction.

Key Features:
- Extraction-only approach: LLM extracts information from input text, never fabricates data
- Multi-provider support: AWS Bedrock, OpenAI, and Anthropic
- Dynamic schema loading: Add schemas without code changes
- Missing field handling: Returns null for fields not found in input

Architecture:
1. Schema Registry: Loads JSON schemas from config/schemas/
2. Transform Tools: Each schema creates a transform_to_{schema_name} tool
3. Field Extraction Engine: Uses LLM to extract fields from unstructured text
"""
# /// script
# dependencies = [
#     "fastmcp>=2.3.0",
#     "boto3>=1.28.0",
#     "botocore>=1.31.0",
#     "jsonschema>=4.0.0",
#     "openai>=1.0.0",
#     "anthropic>=0.25.0",
# ]
# requires-python = ">=3.12"
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

# Support both direct execution and module import
try:
    from .security_config import SecurityValidator, get_secure_config_defaults
except ImportError:
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
# Host must be 0.0.0.0 to accept connections from ALB (not just localhost)
# stateless_http mode is controlled by FASTMCP_STATELESS_HTTP env var
stateless_mode = os.getenv("FASTMCP_STATELESS_HTTP", "false").lower() == "true"
mcp = FastMCP("schema-transform", host="0.0.0.0", port=8000, stateless_http=stateless_mode)
logger.info(f"FastMCP initialized with stateless_http={stateless_mode}")

# Add health check endpoint for ALB
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for ALB."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "service": "schema-transform-mcp"})

# Global variables for model clients
bedrock_runtime = None
openai_client = None
anthropic_client = None

def load_schemas(schemas_dir: str = None) -> Dict[str, Dict[str, Any]]:
    """
    Load JSON schema files from the specified directory or default config directory.
    
    Each schema file defines the structure for a transform tool. The schema name
    (derived from the filename) determines the tool name: transform_to_{schema_name}.
    
    Args:
        schemas_dir: Optional path to schemas directory. If None, uses default
                     config/schemas/ directory relative to this module.
    
    Returns:
        Dictionary mapping schema names to their configuration (description, schema definition)
    """
    schemas = {}
    
    # Get the default directory path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_schemas_dir = os.path.join(script_dir, "config", "schemas")
    
    # Use provided path if it exists, otherwise fall back to default
    if schemas_dir is None:
        schemas_dir = default_schemas_dir
    elif not os.path.exists(schemas_dir):
        logger.warning(f"Configured schemas directory not found: {schemas_dir}")
        logger.info(f"Falling back to default schemas directory: {default_schemas_dir}")
        schemas_dir = default_schemas_dir
    
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
    config_path = os.path.join(script_dir, "config", "config.json")
    
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
    Initialize LLM provider clients for field extraction.
    
    Supports credentials from config file and environment variables (set via MCP config).
    The initialized clients are used by extract_fields() to perform field extraction
    from unstructured text.
    
    Supported providers:
    - AWS Bedrock: Uses boto3 client with AWS credentials
    - OpenAI: Uses OpenAI client with API key
    - Anthropic: Uses Anthropic client with API key
    
    Args:
        config: Configuration dictionary containing provider settings and credentials
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
    
    # Log current provider status
    logger.info(f"Current provider: {provider}")
    if provider == "aws_bedrock" and bedrock_runtime is None:
        logger.warning("AWS Bedrock selected but not available - transformation will return errors until configured")
    elif provider == "openai" and openai_client is None:
        logger.warning("OpenAI selected but not available - transformation will return errors until configured")
    elif provider == "anthropic" and anthropic_client is None:
        logger.warning("Anthropic selected but not available - transformation will return errors until configured")

# Initialize model clients
initialize_model_clients(CONFIG)

# Log schema loading results
if not SCHEMAS:
    logger.warning("No schemas found! Server will start but no schema tools will be available.")
    logger.info("You can add schemas dynamically using the 'add_schema' tool.")
else:
    logger.info(f"Successfully loaded {len(SCHEMAS)} schemas from files: {list(SCHEMAS.keys())}")

def build_extraction_prompt(input_text: str, schema: Dict[str, Any]) -> str:
    """
    Build an extraction-only prompt that instructs the LLM to extract fields from input text.
    
    The prompt explicitly instructs the LLM to:
    - ONLY extract information present in the input text
    - NOT generate, invent, or hallucinate any data
    - Set fields to null if information cannot be found
    - Return only valid JSON matching the schema structure
    
    Args:
        input_text: The free-form text to extract information from
        schema: The JSON schema defining the expected output structure
        
    Returns:
        The formatted extraction prompt ready to send to the LLM
    """
    schema_json = json.dumps(schema, indent=2)
    
    return f"""You are a data extraction assistant. Extract information from the provided text and format it according to the JSON schema below.

CRITICAL RULES:
1. ONLY extract information that is explicitly present in the input text
2. DO NOT generate, invent, or hallucinate any data
3. If a field cannot be found in the input, set it to null
4. Return ONLY valid JSON matching the schema structure
5. Do not include any explanations, markdown formatting, or text outside the JSON structure

Schema:
{schema_json}

Input text to extract from:
{input_text}

Extract the data and return JSON only:"""


def extract_fields(input_text: str, schema_name: str) -> Dict[str, Any]:
    """
    Extract fields from input text according to the schema using the configured LLM provider.
    
    This function uses an LLM to intelligently extract relevant information from
    unstructured text and format it according to the specified schema. The LLM is
    instructed to only extract information present in the input, not generate new content.
    
    Args:
        input_text: The free-form text to extract information from
        schema_name: The name of the schema to use for extraction
        
    Returns:
        Dictionary containing either:
        - Extracted data matching the schema structure (on success)
        - Error information with 'success': False (on failure)
    """
    # Validate input - check for None, empty string, or whitespace-only input
    if input_text is None:
        return {
            "success": False,
            "error": "Input response is empty or invalid: received null input"
        }
    
    if not isinstance(input_text, str):
        return {
            "success": False,
            "error": f"Input response is empty or invalid: expected string, got {type(input_text).__name__}"
        }
    
    if not input_text.strip():
        return {
            "success": False,
            "error": "Input response is empty or invalid: input contains only whitespace"
        }
    
    # Get schema configuration
    schema_config = SCHEMAS.get(schema_name)
    if not schema_config:
        return {
            "success": False,
            "error": f"Schema '{schema_name}' not found"
        }
    
    schema = schema_config.get("schema", {})
    
    # Get extraction configuration
    extraction_config = CONFIG.get("extraction", {})
    provider = extraction_config.get("provider", "")
    model_id = extraction_config.get("model_id", "")
    parameters = extraction_config.get("parameters", {})
    
    logger.info(f"=== EXTRACTING FIELDS ===")
    logger.info(f"Provider: {provider}")
    logger.info(f"Model ID: {model_id}")
    logger.info(f"Schema name: {schema_name}")
    logger.info(f"Input text length: {len(input_text)} characters")
    
    # Check if provider is available
    if not provider:
        return {
            "success": False,
            "error": "LLM provider not configured. Please configure a provider (aws_bedrock, openai, or anthropic) in config.json"
        }
    
    # Validate provider is one of the supported types
    supported_providers = ["aws_bedrock", "openai", "anthropic"]
    if provider not in supported_providers:
        return {
            "success": False,
            "error": f"LLM provider '{provider}' is not supported. Supported providers: {', '.join(supported_providers)}"
        }
    
    # Check if the specific provider client is available
    if provider == "aws_bedrock" and bedrock_runtime is None:
        return {
            "success": False,
            "error": "AWS Bedrock client not available. Please check your AWS credentials and region configuration."
        }
    elif provider == "openai" and openai_client is None:
        return {
            "success": False,
            "error": "OpenAI client not available. Please set the OPENAI_API_KEY environment variable or configure it in config.json."
        }
    elif provider == "anthropic" and anthropic_client is None:
        return {
            "success": False,
            "error": "Anthropic client not available. Please set the ANTHROPIC_API_KEY environment variable or configure it in config.json."
        }
    
    # Build extraction prompt
    extraction_prompt = build_extraction_prompt(input_text, schema)
    
    # Route to appropriate provider
    if provider == "aws_bedrock":
        return extract_with_aws_bedrock(extraction_prompt, schema_name, model_id, parameters)
    elif provider == "openai":
        return extract_with_openai(extraction_prompt, schema_name, model_id, parameters)
    elif provider == "anthropic":
        return extract_with_anthropic(extraction_prompt, schema_name, model_id, parameters)
    else:
        return {
            "success": False,
            "error": f"LLM provider '{provider}' not configured or unavailable"
        }










def extract_with_aws_bedrock(extraction_prompt: str, schema_name: str, model_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract fields using AWS Bedrock model.
    
    Args:
        extraction_prompt: The extraction prompt with input text and schema
        schema_name: The name of the schema being extracted to
        model_id: The Bedrock model ID to use
        parameters: Model parameters (temperature, max_tokens, etc.)
        
    Returns:
        Extracted data or error dictionary
    """
    if bedrock_runtime is None:
        return {
            "success": False,
            "error": "AWS Bedrock client not available. Please check your AWS credentials and region configuration."
        }
    
    try:
        # Prepare the request based on model type
        if "anthropic.claude" in model_id or "us.anthropic.claude" in model_id:
            request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": parameters.get("max_tokens", 4096),
                "temperature": parameters.get("temperature", 0.1),
                "top_p": parameters.get("top_p", 0.9),
                "messages": [{"role": "user", "content": extraction_prompt}]
            }
        elif "amazon.titan" in model_id:
            request = {
                "inputText": extraction_prompt,
                "textGenerationConfig": {
                    "maxTokenCount": parameters.get("max_tokens", 4096),
                    "temperature": parameters.get("temperature", 0.1),
                    "topP": parameters.get("top_p", 0.9)
                }
            }
        else:
            return {
                "success": False,
                "error": f"Unknown Bedrock model type: {model_id}"
            }
        
        logger.info(f"Attempting to extract fields using Bedrock model: {model_id}")
        
        start_time = time.time()
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request)
        )
        end_time = time.time()
        
        logger.info(f"Bedrock extraction call successful in {end_time - start_time:.2f} seconds")
        
        # Parse response based on model type
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        if "anthropic.claude" in model_id or "us.anthropic.claude" in model_id:
            content = response_body['content'][0]['text']
        elif "amazon.titan" in model_id:
            content = response_body['results'][0]['outputText']
        else:
            content = str(response_body)
        
        return parse_extraction_response(content, schema_name)
            
    except Exception as e:
        logger.error(f"Error extracting with Bedrock: {e}")
        return {
            "success": False,
            "error": f"Failed to extract fields: {str(e)}"
        }


def extract_with_openai(extraction_prompt: str, schema_name: str, model_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract fields using OpenAI model.
    
    Args:
        extraction_prompt: The extraction prompt with input text and schema
        schema_name: The name of the schema being extracted to
        model_id: The OpenAI model ID to use
        parameters: Model parameters (temperature, max_tokens, etc.)
        
    Returns:
        Extracted data or error dictionary
    """
    if openai_client is None:
        return {
            "success": False,
            "error": "OpenAI client not available. Please set the OPENAI_API_KEY environment variable or configure it in config.json."
        }
    
    try:
        start_time = time.time()
        response = openai_client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=parameters.get("temperature", 0.1),
            top_p=parameters.get("top_p", 0.9),
            max_tokens=parameters.get("max_tokens", 4096)
        )
        end_time = time.time()
        
        logger.info(f"OpenAI extraction call successful in {end_time - start_time:.2f} seconds")
        
        content = response.choices[0].message.content
        return parse_extraction_response(content, schema_name)
        
    except Exception as e:
        logger.error(f"Error extracting with OpenAI: {e}")
        return {
            "success": False,
            "error": f"Failed to extract fields: {str(e)}"
        }


def extract_with_anthropic(extraction_prompt: str, schema_name: str, model_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract fields using Anthropic model.
    
    Args:
        extraction_prompt: The extraction prompt with input text and schema
        schema_name: The name of the schema being extracted to
        model_id: The Anthropic model ID to use
        parameters: Model parameters (temperature, max_tokens, etc.)
        
    Returns:
        Extracted data or error dictionary
    """
    if anthropic_client is None:
        return {
            "success": False,
            "error": "Anthropic client not available. Please set the ANTHROPIC_API_KEY environment variable or configure it in config.json."
        }
    
    try:
        start_time = time.time()
        response = anthropic_client.messages.create(
            model=model_id,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=parameters.get("temperature", 0.1),
            top_p=parameters.get("top_p", 0.9),
            max_tokens=parameters.get("max_tokens", 4096)
        )
        end_time = time.time()
        
        logger.info(f"Anthropic extraction call successful in {end_time - start_time:.2f} seconds")
        
        content = response.content[0].text
        return parse_extraction_response(content, schema_name)
        
    except Exception as e:
        logger.error(f"Error extracting with Anthropic: {e}")
        return {
            "success": False,
            "error": f"Failed to extract fields: {str(e)}"
        }


def ensure_schema_structure(data: Any, schema: Dict[str, Any]) -> Any:
    """
    Ensure the data conforms to the schema structure, setting missing fields to null.
    
    This function recursively processes the data to ensure all fields defined in the
    schema are present. Missing required fields are set to null rather than being omitted.
    
    Args:
        data: The extracted data (may be partial)
        schema: The JSON schema defining the expected structure
        
    Returns:
        Data with all schema fields present (missing fields set to null)
    """
    schema_type = schema.get("type", "object")
    
    if schema_type == "object":
        properties = schema.get("properties", {})
        
        # If data is not a dict, return a dict with all fields set to null
        if not isinstance(data, dict):
            result = {}
            for field_name, field_schema in properties.items():
                result[field_name] = None
            return result
        
        result = dict(data)  # Copy the data
        
        # Ensure all schema properties exist
        for field_name, field_schema in properties.items():
            if field_name not in result:
                # Field is missing, set to null
                result[field_name] = None
            elif result[field_name] is not None:
                # Field exists and is not null, recursively ensure structure for nested objects
                field_type = field_schema.get("type")
                if field_type == "object":
                    result[field_name] = ensure_schema_structure(result[field_name], field_schema)
                elif field_type == "array":
                    items_schema = field_schema.get("items", {})
                    if isinstance(result[field_name], list) and items_schema.get("type") == "object":
                        result[field_name] = [
                            ensure_schema_structure(item, items_schema) 
                            for item in result[field_name]
                        ]
        
        return result
    
    elif schema_type == "array":
        items_schema = schema.get("items", {})
        
        # If data is not a list, return null
        if not isinstance(data, list):
            return None
        
        # Process each item if items are objects
        if items_schema.get("type") == "object":
            return [ensure_schema_structure(item, items_schema) for item in data]
        
        return data
    
    else:
        # For primitive types, return the data as-is
        return data


def parse_extraction_response(content: str, schema_name: str) -> Dict[str, Any]:
    """
    Parse the LLM response and extract JSON data.
    
    This function parses the LLM response, extracts JSON data, and ensures
    the result conforms to the schema structure. Missing fields are set to null
    to preserve the schema structure even with partial data.
    
    Args:
        content: The raw response content from the LLM
        schema_name: The name of the schema for context
        
    Returns:
        Extracted data dictionary or error dictionary
    """
    # Handle empty or None content
    if content is None:
        logger.error("LLM returned null response")
        return {
            "success": False,
            "error": "Failed to extract fields from input: LLM returned empty response"
        }
    
    if not content.strip():
        logger.error("LLM returned empty response")
        return {
            "success": False,
            "error": "Failed to extract fields from input: LLM returned empty response"
        }
    
    logger.info(f"Parsing extraction response, length: {len(content)} characters")
    
    try:
        # Look for JSON content
        if content.strip().startswith('{') and content.strip().endswith('}'):
            result = json.loads(content.strip())
        else:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # Try to find JSON within the response
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    logger.error(f"No JSON structure found in LLM response: {content[:200]}...")
                    return {
                        "success": False,
                        "error": "Failed to extract fields from input: No valid JSON structure found in LLM response"
                    }
        
        # Ensure the result conforms to the schema structure with missing fields set to null
        schema_config = SCHEMAS.get(schema_name, {})
        schema = schema_config.get("schema", {})
        
        if schema:
            result = ensure_schema_structure(result, schema)
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse extraction response as JSON: {e}")
        logger.error(f"Raw content (first 500 chars): {content[:500]}")
        return {
            "success": False,
            "error": f"Failed to extract fields from input: Invalid JSON in LLM response - {str(e)}"
        }






def create_schema_tool(schema_name: str, schema_config: Dict[str, Any]) -> Callable:
    """
    Create a transform tool function for a given schema.
    
    Args:
        schema_name: Name of the schema
        schema_config: Schema configuration including description and schema definition
        
    Returns:
        A tool function that transforms input text into structured JSON matching the schema
    """
    def transform_tool(response: str) -> Dict[str, Any]:
        """
        Transform unstructured text into structured JSON matching the schema.
        
        Args:
            response: The free-form text (typically from an LLM) to transform
            
        Returns:
            Structured JSON matching the schema, or error information
        """
        logger.info(f"Transforming input to {schema_name} schema")
        
        # Use extract_fields to transform the input text
        return extract_fields(response, schema_name)
    
    # Set function metadata for MCP
    transform_tool.__name__ = f"transform_to_{schema_name}"
    transform_tool.__doc__ = f"""
    Transform unstructured text into {schema_config.get('description', f'{schema_name} format')}.
    
    Args:
        response: The free-form text to transform into structured JSON
    
    Returns:
        Structured JSON matching the {schema_name} schema
    """
    
    return transform_tool

def register_schema_tools():
    """
    Dynamically register transform tools for all loaded schemas.
    
    This function creates and registers transform_to_{schema_name} tools
    for each loaded schema. These tools accept unstructured text and return
    structured JSON matching the schema.
    
    Note: Only transform tools are registered. Content generation tools
    (get_{schema_name}) are NOT supported by this server.
    """
    for schema_name, schema_config in SCHEMAS.items():
        tool_func = create_schema_tool(schema_name, schema_config)
        
        # Register the transform tool with MCP
        mcp.tool()(tool_func)
        logger.info(f"Registered tool: transform_to_{schema_name}")

# Register all schema tools
register_schema_tools()

# Add utility tools
@mcp.tool()
def list_available_schemas() -> Dict[str, Any]:
    """
    List all available schemas and their transform tool names.
    
    Returns a dictionary of all loaded schemas with their descriptions
    and corresponding transform tool names (transform_to_{schema_name}).
    
    Returns:
        Dictionary containing:
        - available_schemas: Map of schema names to their info (name, description, tool_name)
        - total_count: Number of available schemas
    """
    logger.info("Listing available schemas")
    
    schemas_info = {}
    for schema_name, schema_config in SCHEMAS.items():
        schemas_info[schema_name] = {
            "name": schema_name,
            "description": schema_config.get("description", "No description available"),
            "tool_name": f"transform_to_{schema_name}"
        }
    
    return {
        "available_schemas": schemas_info,
        "total_count": len(schemas_info)
    }

@mcp.tool()
def add_schema(schema_name: str, schema_definition: str, description: str = "", system_prompt: str = "") -> Dict[str, Any]:
    """
    Add a new schema by creating a persistent schema file.
    
    Creates a schema file in the config/schemas directory. After adding a schema,
    the server must be restarted for the new transform_to_{schema_name} tool
    to become available.
    
    Args:
        schema_name: Name for the new schema (alphanumeric, underscores, hyphens only)
        schema_definition: JSON schema definition as a string
        description: Optional description of what the schema represents
        system_prompt: Optional extraction hints to guide field extraction
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the result
        - tool_name: The transform tool name (transform_to_{schema_name})
        - restart_required: True (server restart needed)
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
        schemas_dir = os.path.join(script_dir, "config", "schemas")
        
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
            "message": f"Schema '{schema_name}' file created successfully. Restart the MCP server to make the 'transform_to_{schema_name}' tool available.",
            "tool_name": f"transform_to_{schema_name}",
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
def delete_schema(schema_name: str) -> Dict[str, Any]:
    """
    Delete an existing schema file.
    
    Removes a schema file from the config/schemas directory. After deletion,
    the server must be restarted for the transform_to_{schema_name} tool
    to be removed.
    
    Args:
        schema_name: Name of the schema to delete
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the result
        - restart_required: True (server restart needed)
    """
    logger.info(f"Attempting to delete schema: {schema_name}")
    
    try:
        # Validate schema name using security validator
        is_valid, error_msg = SecurityValidator.validate_schema_name(schema_name)
        if not is_valid:
            return {
                "status": "error",
                "message": error_msg
            }
        
        # Get the schemas directory path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schemas_dir = os.path.join(script_dir, "config", "schemas")
        
        # Construct file path
        schema_file_path = os.path.join(schemas_dir, f"{schema_name}.json")
        
        # Validate the file path to prevent directory traversal
        is_valid, error_msg = SecurityValidator.validate_file_path(schema_file_path, schemas_dir)
        if not is_valid:
            return {
                "status": "error",
                "message": f"Invalid file path: {error_msg}"
            }
        
        # Check if file exists
        if not os.path.exists(schema_file_path):
            return {
                "status": "error",
                "message": f"Schema '{schema_name}' does not exist"
            }
        
        # Attempt to delete the file
        try:
            os.remove(schema_file_path)
        except OSError as e:
            return {
                "status": "error",
                "message": f"Failed to delete schema file: {str(e)}"
            }
        
        logger.info(f"Successfully deleted schema file: {schema_file_path}")
        
        return {
            "status": "success",
            "message": f"Schema '{schema_name}' deleted successfully. Restart the MCP server for changes to take effect.",
            "schema_name": schema_name,
            "file_path": schema_file_path,
            "restart_required": True
        }
        
    except Exception as e:
        error_msg = f"Unexpected error deleting schema: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }


def main():
    """
    Entry point for the Schema Transform MCP Server.
    
    Starts the FastMCP server. The transport is determined by the MCP_TRANSPORT
    environment variable:
    - 'stdio' (default): For local CLI usage
    - 'sse': For cloud deployment (ECS Fargate) - legacy but more compatible
    - 'streamable-http': For cloud deployment (newer protocol)
    
    The server provides:
    - transform_to_{schema_name} tools for each loaded schema
    - list_available_schemas, add_schema, delete_schema utility tools
    """
    logger.info("Starting Schema Transform MCP Server")
    logger.info(f"Loaded {len(SCHEMAS)} schemas: {list(SCHEMAS.keys())}")
    
    if not SCHEMAS:
        logger.warning("No schemas loaded! Server will start but no schema tools will be available.")
        logger.info("You can add schemas dynamically using the 'add_schema' tool.")
    
    # Determine transport from environment variable
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    
    if transport in ("streamable-http", "sse"):
        logger.info(f"Starting with {transport} transport (default: 0.0.0.0:8000)")
        logger.info(f"Stateless mode: {os.getenv('FASTMCP_STATELESS_HTTP', 'false')}")
        # FastMCP uses default host/port (0.0.0.0:8000)
        mcp.run(transport=transport)
    else:
        logger.info("Starting with stdio transport")
        mcp.run(transport='stdio')


if __name__ == "__main__":
    main()