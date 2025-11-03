# Fixed Schema MCP Server - Complete Documentation

A Model Context Protocol (MCP) server that dynamically loads JSON schemas and generates structured responses using FastMCP. This server automatically creates tools for any JSON schema you provide, making it completely extensible without code changes. Simply add a schema file and get a corresponding tool instantly.

## Overview

This MCP server provides a flexible, schema-driven approach to generating structured responses. It dynamically loads JSON schema files and creates corresponding MCP tools, allowing you to extend functionality without modifying code. The server supports multiple AI providers (AWS Bedrock, OpenAI, Anthropic) with automatic fallback to mock responses.

## Features

- **Dynamic Schema Loading**: Automatically loads all `.json` files from `config/schemas/`
- **Automatic Tool Generation**: Each schema file becomes a tool named `get_{schema_name}`
- **Custom System Prompts**: Each schema can include specialized AI behavior
- **Multi-Provider Support**: AWS Bedrock, OpenAI, Anthropic, or Mock responses
- **Schema Management**: Built-in tools to list, add, and delete schemas at runtime
- **MCP Configuration**: Set credentials directly in MCP settings
- **Zero Code Changes**: Add unlimited schemas without touching the server code
- **FastMCP Integration**: Built on the FastMCP framework for simplified development
- **Graceful Fallback**: Automatic fallback to mock responses when providers unavailable
- **Security Validation**: Built-in validation to prevent path traversal and injection attacks

## Installation

### Prerequisites

- Python 3.12 or higher
- pip or pipx (Python package managers)
- AWS credentials (optional, for AWS Bedrock integration)

### Method 1: pip Installation

Install the package using pip:

```bash
# Install from source directory
pip install .

# Install with optional AI provider dependencies
pip install .[openai]      # For OpenAI support
pip install .[anthropic]   # For Anthropic support
pip install .[all]         # For all providers

# Install in editable mode for development
pip install -e .
```

After installation, run the server:

```bash
fixed-schema-mcp-server
```

### Method 2: pipx Installation (Recommended for Isolation)

Install in an isolated environment using pipx:

```bash
# Install from source directory
pipx install .

# Install from git repository
pipx install git+https://github.com/yourusername/fixed-schema-mcp-server.git
```

After installation, run the server:

```bash
fixed-schema-mcp-server
```

### Method 3: uv (Development)

For development and testing, use uv:

```bash
# Clone the repository
git clone https://github.com/yourusername/fixed-schema-mcp-server.git
cd fixed-schema-mcp-server/fixed_schema_mcp_server

# Run the server (uv automatically handles dependencies)
uv run fastmcp_server.py
```

### Method 4: Docker

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

### AWS Credentials (Optional)

To use AWS Bedrock for generating responses, configure your AWS credentials using one of these methods:

**Option 1: Environment Variables**

```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Option 2: AWS Profile**

```bash
export AWS_PROFILE="your-profile"
```

**Option 3: MCP Configuration**

Set credentials in your MCP client configuration (see Integration section below).

**Note**: If AWS credentials are not configured, the server will automatically fall back to mock responses.

### AI Provider Configuration

The server supports multiple AI providers. Configure them via environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-proj-your-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# AWS Bedrock (see AWS Credentials above)
```

### Model Configuration

Edit `config/config.json` to customize AI model settings:

```json
{
  "default_provider": "bedrock",
  "bedrock": {
    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "region": "us-east-1"
  },
  "openai": {
    "model": "gpt-4"
  },
  "anthropic": {
    "model": "claude-3-5-sonnet-20241022"
  }
}
```

## Usage

### Starting the Server

**If installed via pip/pipx:**

```bash
fixed-schema-mcp-server
```

**If using uv for development:**

```bash
cd fixed_schema_mcp_server
uv run fastmcp_server.py
```

**With environment variables:**

```bash
AWS_PROFILE=myprofile fixed-schema-mcp-server
```

### Available Tools

The server provides two types of tools:

1. **Schema-Based Tools**: Dynamically generated from JSON schema files (named `get_{schema_name}`)
2. **Utility Tools**: Built-in tools for schema management

### Using Schema-Based Tools

All schema-based tools accept a `query` parameter and return structured responses:

```
@fixed-schema get_weather_report query: "Weather in San Francisco"
@fixed-schema get_product_info query: "iPhone 15 Pro"
@fixed-schema get_recipe query: "chocolate chip cookies"
@fixed-schema get_person_profile query: "Elon Musk"
@fixed-schema get_api_endpoint query: "user authentication API"
@fixed-schema get_troubleshooting_guide query: "computer won't start"
@fixed-schema get_article_summary query: "artificial intelligence"
@fixed-schema get_movie_review query: "The Matrix"
@fixed-schema get_book_review query: "1984 by George Orwell"
@fixed-schema get_sports_stats query: "NBA finals 2024"
```

### Using Utility Tools

**List all available schemas:**

```
@fixed-schema list_available_schemas
```

**Add a new schema:**

```
@fixed-schema add_schema schema_name: "book_review" schema_definition: "{...}" description: "Book review schema"
```

**Delete a schema:**

```
@fixed-schema delete_schema schema_name: "old_schema"
```

Note: After adding or deleting schemas, restart the server for changes to take effect.

## Functions Reference

This section provides detailed documentation for all available tools in the MCP server.

### Schema-Based Tools

Schema-based tools are dynamically generated from JSON schema files in the `config/schemas/` directory. Each schema file automatically creates a corresponding tool named `get_{schema_name}`.

#### Common Parameters

All schema-based tools accept the following parameter:

- **query** (string, required): The input query or request describing what information you want

#### Common Return Format

All schema-based tools return structured JSON data matching their respective schema definitions.

#### Available Schema Tools

##### get_weather_report

Get structured weather information including current conditions and forecasts.

**Parameters:**
- `query` (string): Location or weather query (e.g., "Weather in San Francisco", "Current conditions in Tokyo")

**Returns:**
```json
{
  "location": "string",
  "temperature": "number",
  "conditions": "string",
  "humidity": "number",
  "wind_speed": "number",
  "forecast": [
    {
      "day": "string",
      "high": "number",
      "low": "number",
      "conditions": "string"
    }
  ]
}
```

**Example:**
```
@fixed-schema get_weather_report query: "Weather forecast for Seattle this week"
```

##### get_product_info

Get structured information about products including features, pricing, and descriptions.

**Parameters:**
- `query` (string): Product name or description (e.g., "iPhone 15 Pro", "Sony WH-1000XM5 headphones")

**Returns:**
```json
{
  "name": "string",
  "description": "string",
  "price": "number",
  "category": "string",
  "features": ["string"]
}
```

**Example:**
```
@fixed-schema get_product_info query: "MacBook Pro M3 specifications"
```

##### get_person_profile

Get structured biographical information about individuals including education, career, and achievements.

**Parameters:**
- `query` (string): Person's name or description (e.g., "Elon Musk", "Marie Curie biography")

**Returns:**
```json
{
  "name": "string",
  "bio": "string",
  "expertise": ["string"],
  "achievements": ["string"],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "year": "number"
    }
  ],
  "career": [
    {
      "position": "string",
      "organization": "string",
      "period": "string"
    }
  ],
  "impact": "string"
}
```

**Example:**
```
@fixed-schema get_person_profile query: "Ada Lovelace"
```

##### get_recipe

Get structured recipe information including ingredients, instructions, and nutritional details.

**Parameters:**
- `query` (string): Recipe name or dish (e.g., "chocolate chip cookies", "chicken tikka masala")

**Returns:**
```json
{
  "name": "string",
  "description": "string",
  "prep_time": "number",
  "cook_time": "number",
  "servings": "number",
  "ingredients": [
    {
      "item": "string",
      "amount": "string"
    }
  ],
  "instructions": ["string"],
  "nutrition": {
    "calories": "number",
    "protein": "number",
    "carbs": "number",
    "fat": "number"
  }
}
```

**Example:**
```
@fixed-schema get_recipe query: "homemade pizza dough"
```

##### get_api_endpoint

Get structured API endpoint documentation including parameters, responses, and examples.

**Parameters:**
- `query` (string): API endpoint description (e.g., "user authentication endpoint", "REST API for creating posts")

**Returns:**
```json
{
  "endpoint": "string",
  "method": "string",
  "description": "string",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "required": "boolean",
      "description": "string"
    }
  ],
  "response": {
    "status_code": "number",
    "body": "object"
  },
  "example": "string"
}
```

**Example:**
```
@fixed-schema get_api_endpoint query: "OAuth2 token endpoint"
```

##### get_troubleshooting_guide

Get structured troubleshooting guides with step-by-step solutions.

**Parameters:**
- `query` (string): Problem description (e.g., "computer won't start", "WiFi connection issues")

**Returns:**
```json
{
  "problem": "string",
  "symptoms": ["string"],
  "possible_causes": ["string"],
  "solutions": [
    {
      "step": "number",
      "action": "string",
      "expected_result": "string"
    }
  ],
  "prevention": ["string"]
}
```

**Example:**
```
@fixed-schema get_troubleshooting_guide query: "laptop overheating"
```

##### get_article_summary

Get structured article summaries with key points and takeaways.

**Parameters:**
- `query` (string): Article topic or title (e.g., "artificial intelligence trends", "climate change impacts")

**Returns:**
```json
{
  "title": "string",
  "summary": "string",
  "key_points": ["string"],
  "main_topics": ["string"],
  "conclusion": "string"
}
```

**Example:**
```
@fixed-schema get_article_summary query: "quantum computing breakthroughs"
```

##### get_movie_review

Get structured movie reviews with ratings and analysis.

**Parameters:**
- `query` (string): Movie title (e.g., "The Matrix", "Inception")

**Returns:**
```json
{
  "title": "string",
  "year": "number",
  "genre": ["string"],
  "rating": "number",
  "summary": "string",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "recommendation": "string"
}
```

**Example:**
```
@fixed-schema get_movie_review query: "Blade Runner 2049"
```

##### get_book_review

Get structured book reviews with analysis and recommendations.

**Parameters:**
- `query` (string): Book title and author (e.g., "1984 by George Orwell", "The Great Gatsby")

**Returns:**
```json
{
  "title": "string",
  "author": "string",
  "genre": ["string"],
  "rating": "number",
  "summary": "string",
  "themes": ["string"],
  "strengths": ["string"],
  "target_audience": "string",
  "recommendation": "string"
}
```

**Example:**
```
@fixed-schema get_book_review query: "To Kill a Mockingbird"
```

##### get_sports_stats

Get structured sports statistics and game information.

**Parameters:**
- `query` (string): Sports query (e.g., "NBA finals 2024", "World Cup 2022 statistics")

**Returns:**
```json
{
  "event": "string",
  "date": "string",
  "teams": ["string"],
  "score": "string",
  "key_players": [
    {
      "name": "string",
      "team": "string",
      "stats": "object"
    }
  ],
  "highlights": ["string"],
  "outcome": "string"
}
```

**Example:**
```
@fixed-schema get_sports_stats query: "Super Bowl LVIII highlights"
```

### Utility Tools

Utility tools provide schema management functionality and server information.

#### list_available_schemas

List all available schemas and their descriptions.

**Parameters:** None

**Returns:**
```json
{
  "available_schemas": {
    "schema_name": {
      "name": "string",
      "description": "string",
      "tool_name": "string"
    }
  },
  "total_count": "number"
}
```

**Example:**
```
@fixed-schema list_available_schemas
```

**Use Cases:**
- Discover what schema tools are available
- Check if a specific schema is loaded
- Get tool names for programmatic access

#### add_schema

Add a new schema by creating a persistent schema file. The server must be restarted for the new schema to become available as a tool.

**Parameters:**
- `schema_name` (string, required): Name for the new schema (alphanumeric, underscores, and hyphens only)
- `schema_definition` (string, required): JSON schema definition as a string
- `description` (string, optional): Description of what the schema represents
- `system_prompt` (string, optional): Custom system prompt to guide AI behavior for this schema

**Returns:**
```json
{
  "status": "success" | "error",
  "message": "string",
  "tool_name": "string",
  "schema_name": "string",
  "file_path": "string",
  "restart_required": true
}
```

**Example:**
```
@fixed-schema add_schema schema_name: "company_profile" schema_definition: '{"type": "object", "properties": {"name": {"type": "string"}, "industry": {"type": "string"}, "founded": {"type": "number"}}}' description: "Company information schema"
```

**Security Notes:**
- Schema names are validated to prevent directory traversal attacks
- JSON schema definitions are validated before saving
- System prompts are limited to 2000 characters
- Files are created in the secure `config/schemas/` directory only

**Use Cases:**
- Extend the server with custom schemas without code changes
- Create domain-specific structured response formats
- Prototype new data structures quickly

#### delete_schema

Delete an existing schema file. The server must be restarted for the schema tool to be removed.

**Parameters:**
- `schema_name` (string, required): Name of the schema to delete

**Returns:**
```json
{
  "status": "success" | "error",
  "message": "string",
  "schema_name": "string",
  "file_path": "string",
  "restart_required": true
}
```

**Example:**
```
@fixed-schema delete_schema schema_name: "old_schema"
```

**Error Cases:**
- Schema name validation fails (invalid characters)
- Schema file does not exist
- File system permission errors
- Directory traversal attempt detected

**Use Cases:**
- Remove obsolete or unused schemas
- Clean up test schemas
- Maintain a focused set of production schemas

## Troubleshooting

### AWS Credentials

If you're not seeing responses from AWS Bedrock:

1. Check that your AWS credentials are properly configured:
   ```bash
   aws sts get-caller-identity
   ```

2. Verify that your AWS account has access to Amazon Bedrock and the Claude model.

3. If you don't have AWS credentials, the server will automatically fall back to mock responses.

### Dependencies

If you encounter issues with missing dependencies:

```bash
# Check uv installation
uv --version

# Test dependency resolution
cd fixed_schema_mcp_server
uv run --help
```

### Kiro Integration

If Kiro is not connecting to the MCP server:

1. **Check that the path in the Kiro MCP configuration is correct**
2. **Ensure uv is installed and accessible:**
   ```bash
   which uv
   uv --version
   ```
3. **Try running the server manually to check for errors:**
   ```bash
   cd fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```
4. **Check the absolute path in your Kiro config:**
   ```bash
   pwd  # Run this in the fixed_schema_mcp_server directory
   ```

## How It Works

The FastMCP server works by:

1. Loading schemas from the `config/schemas` directory
2. Registering MCP tools for each schema type
3. When a tool is invoked, it:
   - Constructs a prompt for AWS Bedrock Claude 4 Sonnet
   - Sends the prompt to Claude with the appropriate schema
   - Parses and validates the response against the schema
   - Returns the structured data to Kiro

If AWS Bedrock is not available, it falls back to generating mock responses that match the schema structure.

## Use Cases

- **Product Information**: Get structured information about products
- **Person Profiles**: Generate structured profiles for individuals
- **API Documentation**: Create structured API endpoint documentation
- **Troubleshooting**: Generate step-by-step troubleshooting guides
- **Article Summaries**: Create structured summaries of articles or topics

## Testing

You can test the server using the included test scripts:

```bash
cd fixed_schema_mcp_server

# Test the generic server functionality
python test_generic_server.py

# Test schema loading and tool generation
python -c "
import fastmcp_server
print('Loaded schemas:', list(fastmcp_server.SCHEMAS.keys()))
print('Total tools available:', len(fastmcp_server.SCHEMAS) + 2)  # +2 for utility tools
"

# Test individual tools (if you have a test client)
# uv run test_client.py --query "iPhone 15 Pro" --schema "product_info"
```

## Deployment Options

### Local Development
- Use `uv run fastmcp_server.py` for local development and testing
- Configure with Kiro or Q Chat using the `uv` command approach

### Docker Deployment
- Use the provided Dockerfile for containerized deployment
- Suitable for cloud deployment or isolated environments
- Supports environment variable configuration for AWS credentials

### Cloud Deployment
- The Docker image can be deployed to any container platform (ECS, Kubernetes, etc.)
- Configure AWS credentials via environment variables or IAM roles
- The server uses stdio transport, suitable for process-based communication

## License

This project is licensed under the MIT License - see the LICENSE file for details.