# Fixed Schema MCP Server - Transform Documentation

A Model Context Protocol (MCP) server that transforms unstructured text into structured JSON using user-defined schemas. This server dynamically loads JSON schemas and creates corresponding transform tools, allowing you to convert free-form LLM responses into structured data without code changes.

## Overview

This MCP server provides a schema-driven approach to transforming unstructured text into structured JSON. It dynamically loads JSON schema files and creates corresponding `transform_to_{schema_name}` tools. The server uses an LLM (AWS Bedrock, OpenAI, or Anthropic) to intelligently extract fields from input text - it does NOT generate content, only extracts information that is explicitly present in the input.

## Features

- **Dynamic Schema Loading**: Automatically loads all `.json` files from `config/schemas/`
- **Automatic Transform Tool Generation**: Each schema file becomes a tool named `transform_to_{schema_name}`
- **Extraction-Only Approach**: LLM extracts information from input text, never fabricates data
- **Multi-Provider Support**: AWS Bedrock, OpenAI, or Anthropic for field extraction
- **Schema Management**: Built-in tools to list, add, and delete schemas at runtime
- **MCP Configuration**: Set credentials directly in MCP settings
- **Zero Code Changes**: Add unlimited schemas without touching the server code
- **FastMCP Integration**: Built on the FastMCP framework for simplified development
- **Missing Field Handling**: Returns null for fields not found in input text
- **Security Validation**: Built-in validation to prevent path traversal and injection attacks

## Installation

### Prerequisites

- Python 3.12 or higher
- uv (Python package manager) - [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
- LLM provider credentials (AWS Bedrock, OpenAI, or Anthropic)

### Method 1: uv (Recommended)

For development and testing, use uv:

```bash
# Clone the repository
git clone https://github.com/yourusername/fixed-schema-mcp-server.git
cd fixed-schema-mcp-server/fixed_schema_mcp_server

# Run the server (uv automatically handles dependencies)
uv run fastmcp_server.py
```

### Method 2: uv tool install

Install as a tool using uv:

```bash
# Install from source directory
uv tool install .

# Install from git repository
uv tool install git+https://github.com/yourusername/fixed-schema-mcp-server.git
```

After installation, run the server:

```bash
fixed-schema-mcp-server
```

### Method 3: Docker

For containerized deployment:

```bash
# Build the Docker image
docker build -t fixed-schema-mcp-server .

# Run the container
docker run -it --rm \
  -e AWS_ACCESS_KEY_ID=your_access_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret_key \
  -e AWS_DEFAULT_REGION=us-east-1 \
  fixed-schema-mcp-server
```

## Configuration

### LLM Provider Configuration (Required)

The server requires an LLM provider for field extraction. Configure one of the following:

**AWS Bedrock:**

```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"
```

Or use an AWS profile:

```bash
export AWS_PROFILE="your-profile"
```

**OpenAI:**

```bash
export OPENAI_API_KEY="sk-proj-your-key"
```

**Anthropic:**

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### Extraction Configuration

Edit `config/config.json` to configure the extraction settings:

```json
{
  "server": {
    "name": "schema-transform",
    "log_level": "info"
  },
  "extraction": {
    "provider": "aws_bedrock",
    "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "parameters": {
      "temperature": 0.1,
      "max_tokens": 4096
    }
  },
  "schemas": {
    "path": null
  }
}
```

Note: Low temperature (0.1) is recommended for extraction to ensure deterministic, accurate results.

## Usage

### Starting the Server

**If installed via uv tool:**

```bash
fixed-schema-mcp-server
```

**If running from source:**

```bash
cd fixed_schema_mcp_server
uv run fastmcp_server.py
```

**With environment variables:**

```bash
AWS_PROFILE=myprofile uv run fastmcp_server.py
```

### Available Tools

The server provides two types of tools:

1. **Transform Tools**: Dynamically generated from JSON schema files (named `transform_to_{schema_name}`)
2. **Utility Tools**: Built-in tools for schema management

### Using Transform Tools

All transform tools accept a `response` parameter containing the text to transform:

```
@fixed-schema transform_to_weather_report response: "The weather in San Francisco today is sunny with a high of 72°F and low of 58°F. Humidity is at 65% with winds from the west at 12 mph."

@fixed-schema transform_to_product_info response: "The iPhone 15 Pro is Apple's flagship smartphone priced at $999. It features a titanium design, A17 Pro chip, and a 48MP camera system."

@fixed-schema transform_to_recipe response: "To make chocolate chip cookies, you'll need 2 cups flour, 1 cup butter, 1 cup sugar, 2 eggs, and 1 cup chocolate chips. Mix ingredients, form into balls, and bake at 350°F for 12 minutes. Makes 24 cookies."

@fixed-schema transform_to_person_profile response: "Elon Musk is the CEO of Tesla and SpaceX. He studied physics at the University of Pennsylvania and has led the development of electric vehicles and reusable rockets."
```

### Using Utility Tools

**List all available schemas:**

```
@fixed-schema list_available_schemas
```

**Add a new schema:**

```
@fixed-schema add_schema schema_name: "company_profile" schema_definition: '{"type": "object", "properties": {"name": {"type": "string"}, "industry": {"type": "string"}, "founded": {"type": "number"}}}' description: "Company information schema"
```

**Delete a schema:**

```
@fixed-schema delete_schema schema_name: "old_schema"
```

Note: After adding or deleting schemas, restart the server for changes to take effect.

## Functions Reference

### Transform Tools

Transform tools are dynamically generated from JSON schema files in the `config/schemas/` directory. Each schema file automatically creates a corresponding tool named `transform_to_{schema_name}`.

#### Common Parameters

All transform tools accept the following parameter:

- **response** (string, required): The unstructured text to transform into structured JSON

#### Common Behavior

- **Extraction Only**: The LLM extracts information present in the input text
- **No Fabrication**: Fields not found in the input are set to `null`
- **Schema Conformance**: Output always matches the schema structure

#### Available Transform Tools

##### transform_to_weather_report

Transform weather-related text into structured weather data.

**Parameters:**
- `response` (string): Text containing weather information

**Returns:**
```json
{
  "location": "string or null",
  "temperature": "number or null",
  "conditions": "string or null",
  "humidity": "number or null",
  "wind_speed": "number or null",
  "forecast": "array or null"
}
```

**Example:**
```
@fixed-schema transform_to_weather_report response: "Seattle is experiencing rain today with temperatures around 55°F. Humidity is 80% with 10 mph winds."
```

##### transform_to_product_info

Transform product descriptions into structured product data.

**Parameters:**
- `response` (string): Text containing product information

**Returns:**
```json
{
  "name": "string or null",
  "description": "string or null",
  "price": "number or null",
  "category": "string or null",
  "features": "array or null"
}
```

**Example:**
```
@fixed-schema transform_to_product_info response: "The MacBook Pro M3 is a professional laptop with 18-hour battery life, priced at $1999."
```

##### transform_to_person_profile

Transform biographical text into structured profile data.

**Parameters:**
- `response` (string): Text containing information about a person

**Returns:**
```json
{
  "name": "string or null",
  "bio": "string or null",
  "expertise": "array or null",
  "achievements": "array or null",
  "education": "array or null",
  "career": "array or null",
  "impact": "string or null"
}
```

##### transform_to_recipe

Transform recipe descriptions into structured recipe data.

**Parameters:**
- `response` (string): Text containing recipe information

**Returns:**
```json
{
  "name": "string or null",
  "description": "string or null",
  "prep_time": "number or null",
  "cook_time": "number or null",
  "servings": "number or null",
  "ingredients": "array or null",
  "instructions": "array or null",
  "nutrition": "object or null"
}
```

##### transform_to_api_endpoint

Transform API documentation text into structured endpoint data.

**Parameters:**
- `response` (string): Text containing API endpoint information

**Returns:**
```json
{
  "endpoint": "string or null",
  "method": "string or null",
  "description": "string or null",
  "parameters": "array or null",
  "response": "object or null",
  "example": "string or null"
}
```

##### transform_to_troubleshooting_guide

Transform troubleshooting text into structured guide data.

**Parameters:**
- `response` (string): Text containing troubleshooting information

**Returns:**
```json
{
  "problem": "string or null",
  "symptoms": "array or null",
  "possible_causes": "array or null",
  "solutions": "array or null",
  "prevention": "array or null"
}
```

##### transform_to_article_summary

Transform article text into structured summary data.

**Parameters:**
- `response` (string): Text containing article content

**Returns:**
```json
{
  "title": "string or null",
  "summary": "string or null",
  "key_points": "array or null",
  "main_topics": "array or null",
  "conclusion": "string or null"
}
```

##### transform_to_movie_review

Transform movie review text into structured review data.

**Parameters:**
- `response` (string): Text containing movie review information

**Returns:**
```json
{
  "title": "string or null",
  "year": "number or null",
  "genre": "array or null",
  "rating": "number or null",
  "summary": "string or null",
  "strengths": "array or null",
  "weaknesses": "array or null",
  "recommendation": "string or null"
}
```

##### transform_to_book_review

Transform book review text into structured review data.

**Parameters:**
- `response` (string): Text containing book review information

**Returns:**
```json
{
  "title": "string or null",
  "author": "string or null",
  "genre": "array or null",
  "rating": "number or null",
  "summary": "string or null",
  "themes": "array or null",
  "strengths": "array or null",
  "target_audience": "string or null",
  "recommendation": "string or null"
}
```

##### transform_to_sports_stats

Transform sports text into structured statistics data.

**Parameters:**
- `response` (string): Text containing sports information

**Returns:**
```json
{
  "event": "string or null",
  "date": "string or null",
  "teams": "array or null",
  "score": "string or null",
  "key_players": "array or null",
  "highlights": "array or null",
  "outcome": "string or null"
}
```

### Utility Tools

#### list_available_schemas

List all available schemas and their transform tool names.

**Parameters:** None

**Returns:**
```json
{
  "available_schemas": {
    "schema_name": {
      "name": "string",
      "description": "string",
      "tool_name": "transform_to_{schema_name}"
    }
  },
  "total_count": "number"
}
```

#### add_schema

Add a new schema by creating a persistent schema file.

**Parameters:**
- `schema_name` (string, required): Name for the new schema
- `schema_definition` (string, required): JSON schema definition as a string
- `description` (string, optional): Description of the schema
- `system_prompt` (string, optional): Custom extraction hints

**Returns:**
```json
{
  "status": "success",
  "message": "string",
  "tool_name": "transform_to_{schema_name}",
  "restart_required": true
}
```

#### delete_schema

Delete an existing schema file.

**Parameters:**
- `schema_name` (string, required): Name of the schema to delete

**Returns:**
```json
{
  "status": "success",
  "message": "string",
  "restart_required": true
}
```

## Error Handling

The server returns structured error responses:

| Error Type | Response |
|------------|----------|
| Empty input | `{"success": false, "error": "Input response is empty or invalid"}` |
| Schema not found | `{"success": false, "error": "Schema '{name}' not found"}` |
| Provider unavailable | `{"success": false, "error": "LLM provider not configured"}` |
| Extraction failure | `{"success": false, "error": "Failed to extract fields from input"}` |

## How It Works

The transform server works by:

1. Loading schemas from the `config/schemas` directory
2. Registering `transform_to_{schema_name}` tools for each schema
3. When a transform tool is invoked:
   - Validates the input text is not empty
   - Builds an extraction-only prompt with the schema
   - Sends the prompt to the configured LLM provider
   - Parses the JSON response
   - Ensures all schema fields are present (missing fields set to null)
   - Returns the structured data

The LLM is explicitly instructed to:
- ONLY extract information present in the input text
- NOT generate, invent, or hallucinate any data
- Set fields to null if information cannot be found

## Troubleshooting

### LLM Provider Issues

If transformations are failing:

1. **Check provider configuration** in `config/config.json`
2. **Verify credentials** are set correctly
3. **Test provider access** manually

For AWS Bedrock:
```bash
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-east-1
```

### Empty or Null Results

If all fields are returning null:
- Ensure the input text contains relevant information
- Check that the schema fields match the type of data in the input
- Review the extraction prompt in logs

### Kiro Integration

If Kiro is not connecting to the MCP server:

1. Check that the path in the Kiro MCP configuration is correct
2. Ensure uv is installed and accessible
3. Try running the server manually to check for errors:
   ```bash
   cd fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```

## Testing

```bash
cd fixed_schema_mcp_server

# Run property-based tests
python -m pytest test_extraction_properties.py -v

# Test schema loading
python -c "
import fastmcp_server
print('Loaded schemas:', list(fastmcp_server.SCHEMAS.keys()))
"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
