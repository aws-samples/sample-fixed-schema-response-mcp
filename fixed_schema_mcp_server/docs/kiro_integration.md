# Kiro Integration Guide for FastMCP Edition

This guide explains how to integrate the Fixed Schema Response MCP Server (FastMCP Edition) with Kiro.

## Prerequisites

- Kiro installed and configured
- Fixed Schema MCP Server setup completed (run `./setup.sh` first)
- AWS credentials configured (optional, for AWS Bedrock integration)

## Setup

Before configuring Kiro, make sure you've completed the setup:

```bash
# Run the setup script (only needed once)
./setup.sh
```

This will:
- Create a virtual environment
- Install required dependencies (fastmcp, boto3, jsonschema)
- Make the run script executable

## Configuration

### 1. Create or Update Kiro MCP Configuration

Create or update the file `.kiro/settings/mcp.json` with the following content:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "/path/to/fixed_schema_mcp_server/run_fastmcp.sh",
      "args": [],
      "env": {
        "FASTMCP_LOG_LEVEL": "DEBUG"
      },
      "disabled": false,
      "autoApprove": [
        "get_product_info",
        "get_article_summary",
        "get_person_profile",
        "get_api_endpoint",
        "get_troubleshooting_guide"
      ]
    }
  }
}
```

Make sure to update the `command` path to the absolute path of your `run_fastmcp.sh` script.

### 2. Create a Steering File (Optional)

Create a steering file at `.kiro/steering/fixed-schema-mcp.md` to provide guidance on using the MCP server:

```markdown
---
inclusion: manual
---

# Fixed Schema Response MCP Server (FastMCP Edition)

This steering file provides information about using the Fixed Schema Response MCP Server with Kiro.

## Available Tools

The Fixed Schema MCP Server provides the following tools:

### 1. Product Info (`get_product_info`)
- For generating structured information about products
- Example: `@fixed-schema get_product_info product_name: "iPhone 15 Pro"`

### 2. Article Summary (`get_article_summary`)
- For generating structured summaries of articles or topics
- Example: `@fixed-schema get_article_summary topic: "artificial intelligence"`

### 3. Person Profile (`get_person_profile`)
- For generating structured biographical information about people
- Example: `@fixed-schema get_person_profile person_name: "Elon Musk"`

### 4. API Endpoint Documentation (`get_api_endpoint`)
- For generating structured API endpoint documentation
- Example: `@fixed-schema get_api_endpoint endpoint_name: "user authentication"`

### 5. Troubleshooting Guide (`get_troubleshooting_guide`)
- For generating structured technical troubleshooting guides
- Example: `@fixed-schema get_troubleshooting_guide issue: "computer won't start"`
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
@fixed-schema get_product_info product_name: "iPhone 15 Pro"
@fixed-schema get_person_profile person_name: "Elon Musk"
@fixed-schema get_api_endpoint endpoint_name: "user authentication"
@fixed-schema get_troubleshooting_guide issue: "computer won't start"
@fixed-schema get_article_summary topic: "artificial intelligence"
```

### 3. Include the Steering File (Optional)

To include the steering file in your conversation:

```
#fixed-schema-mcp
```

## Troubleshooting

### Server Connection Issues

If you have trouble connecting to the server:

1. Check that the server is running:
   ```bash
   ./run_fastmcp.sh
   ```

2. Verify that the path in the Kiro MCP configuration is correct

3. Check that the run_fastmcp.sh script has execute permissions:
   ```bash
   chmod +x run_fastmcp.sh
   ```

### AWS Credentials

If you're not seeing responses from AWS Bedrock:

1. Check that your AWS credentials are properly configured:
   ```bash
   aws sts get-caller-identity
   ```

2. Verify that your AWS account has access to Amazon Bedrock and the Claude model.

3. If you don't have AWS credentials, the server will automatically fall back to mock responses.

## Advanced Configuration

### Creating Custom Schemas

To create a custom schema, add a new JSON file to the `test_config/schemas` directory with the following structure:

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
  }
}
```

Then update the `fastmcp_server.py` file to add a new tool function for your schema.