# Fixed Schema Response MCP Server

A Model Context Protocol (MCP) server that processes user queries and returns responses in a fixed schema format (e.g., JSON). Similar to OpenAI's Structured Outputs feature, this MCP server constrains model responses to follow a predefined structure, making outputs more predictable and easier to parse programmatically.

## Features

- **Schema-Based Responses**: Define JSON schemas to structure AI-generated content
- **Schema Validation**: Automatically validate responses against defined schemas
- **Error Handling**: Properly formatted error responses that follow the schema
- **Dynamic Configuration**: Update schemas and settings without server restart
- **Kiro Integration**: Seamlessly works with Kiro as an MCP server
- **Multiple Model Support**: Works with Amazon Bedrock (Claude) and OpenAI models

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- AWS credentials configured (if using Amazon Bedrock)

### Install from PyPI

```bash
pip install fixed-schema-mcp-server
```

### Install from Source

```bash
git clone https://github.com/yourusername/fixed-schema-mcp-server.git
cd fixed-schema-mcp-server
pip install -e .
```

## Quick Start

### 1. Create a Configuration File

#### For Amazon Bedrock (Claude):

```json
{
  "server": {
    "host": "localhost",
    "port": 8000,
    "log_level": "info"
  },
  "model": {
    "provider": "bedrock",
    "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "region": "us-east-1",
    "parameters": {
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 1000
    }
  },
  "schemas": {
    "path": "./schemas",
    "default_schema": "product_info"
  }
}
```

#### For OpenAI:

```json
{
  "server": {
    "host": "localhost",
    "port": 8000,
    "log_level": "info"
  },
  "model": {
    "provider": "openai",
    "model_name": "gpt-4",
    "api_key": "YOUR_API_KEY",
    "parameters": {
      "temperature": 0.7,
      "top_p": 1.0,
      "max_tokens": 1000
    }
  },
  "schemas": {
    "path": "./schemas",
    "default_schema": "product_info"
  }
}
```

### 2. Create a Schema

Create a directory named `schemas` and add a schema file:

```json
{
  "name": "product_info",
  "description": "Schema for product information responses",
  "schema": {
    "type": "object",
    "required": ["name", "description", "price", "category"],
    "properties": {
      "name": {
        "type": "string",
        "description": "The name of the product"
      },
      "description": {
        "type": "string",
        "description": "A detailed description of the product"
      },
      "price": {
        "type": "number",
        "description": "The price of the product in USD"
      },
      "category": {
        "type": "string",
        "description": "The category the product belongs to"
      },
      "features": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "List of product features"
      }
    }
  },
  "system_prompt": "You are a product information assistant. Provide information about products in a structured format."
}
```

### 3. Configure AWS Credentials (for Bedrock)

If using Amazon Bedrock, ensure your AWS credentials are properly configured:

```bash
# Configure AWS CLI
aws configure
```

You'll need to enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (choose a region where Bedrock is available, like us-east-1 or us-west-2)
- Default output format (json)

Make sure your AWS account has access to Amazon Bedrock and the Claude model.

### 4. Start the Server

```bash
fixed-schema-mcp-server --config config.json
```

### 5. Configure Kiro

Add the following to your Kiro MCP configuration:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "fixed-schema-mcp-server",
      "args": ["--config", "config.json"],
      "env": {
        "FIXED_SCHEMA_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Troubleshooting MCP Server Connection

If you encounter issues connecting the MCP server to Kiro, try these steps:

### 1. Check Port Availability

Make sure the port specified in your config.json is available:

```bash
# Check if port 8000 is in use
lsof -i :8000
```

If the port is in use, change it in your config.json.

### 2. Use Absolute Paths

Use absolute paths in your configuration to avoid path resolution issues:

```json
{
  "schemas": {
    "path": "/absolute/path/to/schemas",
    "default_schema": "product_info"
  }
}
```

### 3. Check Dependencies

Ensure all required dependencies are installed:

```bash
pip install -r requirements.txt
```

### 4. Use a Virtual Environment

Create a dedicated virtual environment for the MCP server:

```bash
python -m venv fixed_schema_mcp_venv
source fixed_schema_mcp_venv/bin/activate
pip install -e .
```

### 5. Create a Wrapper Script

If you're having issues with the MCP protocol, create a wrapper script:

```bash
#!/bin/bash
# run_mcp.sh

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set up the virtual environment path
VENV_PATH="${SCRIPT_DIR}/../fixed_schema_mcp_venv"

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Run the server
python "$SCRIPT_DIR/run_server.py" "$@"
```

Then update your Kiro configuration:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "/path/to/run_mcp.sh",
      "args": [
        "--config",
        "/path/to/config.json",
        "--log-level",
        "INFO"
      ]
    }
  }
}
```

### 6. Check Logs

Enable detailed logging to troubleshoot connection issues:

```bash
fixed-schema-mcp-server --config config.json --log-level DEBUG
```

## Testing

You can test the server using the included test client:

```bash
# Test with the product_info schema
python test_client.py "Tell me about the latest iPhone" --schema product_info

# Test with another schema
python test_client.py "Summarize the latest news about AI advancements" --schema article_summary
```

## Documentation

For more detailed information, check out:

- [Installation Guide](fixed_schema_mcp_server/docs/installation/README.md)
- [Schema Documentation](fixed_schema_mcp_server/docs/schema/README.md)
- [API Reference](fixed_schema_mcp_server/docs/api/README.md)
- [Troubleshooting](fixed_schema_mcp_server/docs/troubleshooting/README.md)
- [Performance Tuning](fixed_schema_mcp_server/docs/performance/README.md)

## Use Cases

- **API Development**: Generate structured data for API responses
- **Data Extraction**: Extract specific information from unstructured text
- **Form Filling**: Generate structured data for form submissions
- **Content Generation**: Create structured content for websites or applications
- **Data Transformation**: Convert between different data formats

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.