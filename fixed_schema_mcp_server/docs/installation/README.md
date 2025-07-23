# Installation and Setup Guide

## Installation

### Prerequisites

Before installing the Fixed Schema Response MCP Server, ensure you have the following prerequisites:

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

### Installation Methods

#### Method 1: Install from PyPI

The simplest way to install the Fixed Schema Response MCP Server is via pip:

```bash
pip install fixed-schema-mcp-server
```

#### Method 2: Install from Source

To install from source:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fixed-schema-mcp-server.git
   cd fixed-schema-mcp-server
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

## Configuration

### Basic Configuration

The Fixed Schema Response MCP Server uses a JSON configuration file. Create a file named `config.json` with the following structure:

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
    "default_schema": "default"
  }
}
```

### Configuration Options

#### Server Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `host` | The host address to bind the server | `localhost` |
| `port` | The port to listen on | `8000` |
| `log_level` | Logging level (`debug`, `info`, `warning`, `error`) | `info` |

#### Model Configuration

| Option | Description | Required |
|--------|-------------|----------|
| `provider` | The model provider (e.g., `openai`, `anthropic`) | Yes |
| `model_name` | The name of the model to use | Yes |
| `api_key` | API key for the model provider | Yes |
| `parameters` | Default parameters for model requests | No |

#### Schema Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `path` | Path to the directory containing schema files | `./schemas` |
| `default_schema` | The default schema to use if none is specified | `default` |

### Environment Variables

You can also configure the server using environment variables:

- `FIXED_SCHEMA_MCP_CONFIG_PATH`: Path to the configuration file
- `FIXED_SCHEMA_MCP_MODEL_API_KEY`: API key for the model provider
- `FIXED_SCHEMA_MCP_LOG_LEVEL`: Logging level

## Quickstart Tutorial

### 1. Install the Server

```bash
pip install fixed-schema-mcp-server
```

### 2. Create a Configuration File

Create a file named `config.json`:

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
    "api_key": "YOUR_API_KEY"
  },
  "schemas": {
    "path": "./schemas",
    "default_schema": "product_info"
  }
}
```

### 3. Create a Schema

Create a directory named `schemas` and add a file named `product_info.json`:

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

### 4. Start the Server

```bash
fixed-schema-mcp-server --config config.json
```

### 5. Configure Kiro to Use the Server

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

### 6. Test the Server

Send a request to the server:

```json
{
  "query": "Tell me about the latest iPhone",
  "schema": "product_info"
}
```

You should receive a structured response following the product_info schema.

## Next Steps

- Learn more about [schema definitions](../schema/README.md)
- Explore the [API documentation](../api/README.md)
- Check out the [troubleshooting guide](../troubleshooting/README.md) if you encounter issues