# Kiro Integration Guide

This guide explains how to integrate the Fixed Schema Response MCP Server with Kiro.

## Prerequisites

- Kiro installed and configured
- Fixed Schema Response MCP Server installed
- AWS credentials configured (if using Bedrock)

## Configuration

### 1. Create or Update Kiro MCP Configuration

Create or update the file `.kiro/settings/mcp.json` with the following content:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "python",
      "args": ["fixed_schema_mcp_server/run_server.py", "--config", "fixed_schema_mcp_server/test_config/config.json", "--log-level", "INFO"],
      "env": {
        "FIXED_SCHEMA_MCP_LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": ["product_info", "article_summary", "person_profile", "api_endpoint", "troubleshooting_guide"]
    }
  }
}
```

### 2. Create a Steering File (Optional)

Create a steering file at `.kiro/steering/fixed-schema-mcp.md` to provide guidance on using the MCP server:

```markdown
---
inclusion: manual
---

# Fixed Schema Response MCP Server

This steering file provides information about using the Fixed Schema Response MCP Server with Kiro.

## Available Schemas

The Fixed Schema MCP Server supports the following schemas:

### 1. Product Info (`product_info`)
- For generating structured information about products

### 2. Article Summary (`article_summary`)
- For generating structured summaries of articles or topics

### 3. Person Profile (`person_profile`)
- For generating structured biographical information about people

### 4. API Endpoint Documentation (`api_endpoint`)
- For generating structured API endpoint documentation

### 5. Troubleshooting Guide (`troubleshooting_guide`)
- For generating structured technical troubleshooting guides

## Usage Examples

To use the Fixed Schema MCP Server in Kiro, use the following format:

```
@fixed-schema <query> --schema <schema_name>
```
```

## Usage

### 1. Connect to the MCP Server

1. Open Kiro
2. Use the command palette to search for "MCP"
3. Select "Connect to MCP Server"
4. Choose "fixed-schema" from the list

### 2. Use the MCP Server

Once connected, you can use the MCP server by typing commands like:

```
@fixed-schema Tell me about the latest iPhone --schema product_info
```

### 3. Include the Steering File (Optional)

To include the steering file in your conversation:

```
#fixed-schema-mcp
```

## Troubleshooting

### Server Connection Issues

If you have trouble connecting to the server:

1. Check that the server is running
2. Verify that the configuration file is correct
3. Check the server logs for errors

### Schema Validation Errors

If you get schema validation errors:

1. Make sure you're using a valid schema name
2. Check that your query is appropriate for the schema
3. Try a different query or schema

## Advanced Configuration

### Using Mock Model for Testing

To use the mock model instead of Bedrock:

```json
{
  "server": {
    "host": "localhost",
    "port": 8000,
    "log_level": "info"
  },
  "model": {
    "provider": "mock",
    "model_id": "mock-claude-3-5-sonnet",
    "parameters": {
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 1000
    }
  },
  "schemas": {
    "path": "./test_config/schemas",
    "default_schema": "product_info"
  }
}
```

### Creating Custom Schemas

To create a custom schema, add a new JSON file to the `schemas` directory with the following structure:

```json
{
  "name": "schema_name",
  "description": "Description of the schema's purpose",
  "schema": {
    "type": "object",
    "required": ["field1", "field2"],
    "properties": {
      "field1": {
        "type": "string",
        "description": "Description of field1"
      },
      "field2": {
        "type": "number",
        "description": "Description of field2"
      }
    }
  },
  "system_prompt": "System prompt to guide the model's response"
}
```