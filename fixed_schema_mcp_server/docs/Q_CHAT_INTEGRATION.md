# Q Chat Integration Guide

This guide explains how to integrate the Generic Schema MCP Server with Q Chat. This server dynamically loads JSON schemas and creates corresponding tools automatically.

## Prerequisites

- Q Chat installed and configured
- Python 3.10 or higher
- Generic Schema MCP Server installed or downloaded

## Installation Options

You can run the MCP server in two ways:

### Option A: Install via pip/pipx (Recommended)

Install the package globally or in an isolated environment:

```bash
# Using pip
pip install fixed-schema-mcp-server

# Using pipx (isolated environment)
pipx install fixed-schema-mcp-server

# Or install from source
cd fixed_schema_mcp_server
pip install .
```

### Option B: Run from Source with uv

If you prefer to run from source without installing:

1. Install `uv` package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
2. Clone or download the Generic Schema MCP Server

## Configuration

### Step 1: Locate Q Chat's MCP Configuration

Q Chat's MCP configuration is typically located in one of these files:

**Option A: User-level configuration**
```bash
~/.config/qchat/mcp.json
```

**Option B: Application-level configuration**
```bash
~/.qchat/config.json
```

**Option C: In Q Chat's installation directory**
```bash
/path/to/qchat/config/mcp.json
```

### Step 2: Add Generic Schema MCP Server

Choose the configuration that matches your installation method:

#### Configuration for pip/pipx Installation

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "fixed-schema-mcp-server",
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": [
        "get_product_info",
        "get_article_summary", 
        "get_person_profile",
        "get_api_endpoint",
        "get_troubleshooting_guide",
        "list_available_schemas",
        "add_schema",
        "delete_schema"
      ]
    }
  }
}
```

#### Configuration for uv Run from Source

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": [
        "--directory", 
        "/ABSOLUTE/PATH/TO/YOUR/PROJECT/fixed_schema_mcp_server", 
        "run", 
        "fastmcp_server.py"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": [
        "get_product_info",
        "get_article_summary", 
        "get_person_profile",
        "get_api_endpoint",
        "get_troubleshooting_guide",
        "list_available_schemas",
        "add_schema",
        "delete_schema"
      ]
    }
  }
}
```

**Important**: Replace `/ABSOLUTE/PATH/TO/YOUR/PROJECT/fixed_schema_mcp_server` with your actual path, for example:
```
/path/to/your/fixed_schema_mcp_server
```

### Step 3: Complete Configuration Example

If Q Chat already has other MCP servers configured, your complete configuration might look like:

**Using pip/pipx installation:**
```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "fixed-schema-mcp-server",
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": [
        "get_product_info",
        "get_article_summary", 
        "get_person_profile",
        "get_api_endpoint",
        "get_troubleshooting_guide"
      ]
    },
    "other-mcp-server": {
      "command": "other-command",
      "args": ["other-args"]
    }
  }
}
```

**Using uv run from source:**
```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": [
        "--directory", 
        "/path/to/your/fixed_schema_mcp_server", 
        "run", 
        "fastmcp_server.py"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": [
        "get_product_info",
        "get_article_summary", 
        "get_person_profile",
        "get_api_endpoint",
        "get_troubleshooting_guide"
      ]
    },
    "other-mcp-server": {
      "command": "other-command",
      "args": ["other-args"]
    }
  }
}
```

## Usage in Q Chat

Once configured, you can use the Generic Schema MCP Server tools in your Q Chat conversations:

### Quick Test Examples

Test the server with these simple commands:

```
@fixed-schema list_available_schemas
@fixed-schema get_weather_report query: "Weather in San Francisco"
@fixed-schema get_product_info query: "iPhone 15 Pro"
@fixed-schema get_recipe query: "chocolate chip cookies"
```

### Available Tools

**Schema-Based Tools** (dynamically generated):

1. **Weather Reports**
   ```
   @fixed-schema get_weather_report query: "Weather in San Francisco"
   ```

2. **Product Information**
   ```
   @fixed-schema get_product_info query: "iPhone 15 Pro"
   ```

3. **Cooking Recipes**
   ```
   @fixed-schema get_recipe query: "chocolate chip cookies"
   ```

4. **Person Profiles**
   ```
   @fixed-schema get_person_profile query: "Elon Musk"
   ```

5. **API Documentation**
   ```
   @fixed-schema get_api_endpoint query: "user authentication API"
   ```

6. **Troubleshooting Guides**
   ```
   @fixed-schema get_troubleshooting_guide query: "computer won't start"
   ```

7. **Article Summaries**
   ```
   @fixed-schema get_article_summary query: "artificial intelligence"
   ```

8. **Movie Reviews**
   ```
   @fixed-schema get_movie_review query: "The Matrix"
   ```

**Utility Tools**:

9. **List Available Schemas**
   ```
   @fixed-schema list_available_schemas
   ```

10. **Add Custom Schemas**
    ```
    @fixed-schema add_schema schema_name: "my_custom_schema" schema_definition: "{...}" description: "My custom schema"
    ```



### Example Conversation

```
You: @fixed-schema get_product_info query: "MacBook Pro M3"

Q Chat: {
  "name": "MacBook Pro M3",
  "description": "Apple's latest professional laptop featuring the M3 chip...",
  "price": 1999.99,
  "category": "Laptops",
  "features": ["M3 chip", "16GB RAM", "512GB SSD", "14-inch display"],
  "rating": 4.8,
  "inStock": true
}
```

## Troubleshooting

### Issue: Q Chat Can't Find the MCP Server

**Symptoms:**
- Error message: "MCP server not found" or "Failed to connect"
- No response from the server

**Solutions:**

1. **Verify the absolute path is correct:**
   ```bash
   ls -la /path/to/your/fixed_schema_mcp_server/fastmcp_server.py
   ```

2. **Test the server manually:**
   
   If installed via pip/pipx:
   ```bash
   fixed-schema-mcp-server
   ```
   
   If running from source:
   ```bash
   cd /path/to/your/fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```

3. **Check Q Chat's logs** for detailed error messages

### Issue: Dependencies Not Found

**Symptoms:**
- Error about missing `fastmcp`, `boto3`, or other dependencies
- Import errors

**Solutions:**

1. **Ensure uv is installed:**
   ```bash
   uv --version
   ```

2. **Test dependency installation:**
   ```bash
   cd /path/to/your/fixed_schema_mcp_server
   uv run --help
   ```

### Issue: Tools Not Available

**Symptoms:**
- Q Chat doesn't recognize `@fixed-schema` commands
- Tools don't appear in Q Chat's tool list

**Solutions:**

1. **Check the autoApprove list** in your configuration
2. **Restart Q Chat** after configuration changes
3. **Verify the server is running** by checking Q Chat's MCP status

### Issue: AWS Bedrock Not Working

**Symptoms:**
- Getting mock responses instead of real AI-generated content
- Warning about AWS credentials

**Solutions:**

1. **Configure AWS credentials:**
   ```bash
   aws configure
   ```

2. Or **Set environment variables:**
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

3. **Note**: If AWS credentials are not configured, the server will automatically fall back to mock responses, which is perfectly fine for testing.

## Advanced Configuration

### Custom Environment Variables

You can add custom environment variables to the MCP configuration:

**For pip/pipx installation:**
```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "fixed-schema-mcp-server",
      "env": {
        "FASTMCP_LOG_LEVEL": "DEBUG",
        "AWS_DEFAULT_REGION": "us-west-2",
        "MCP_TIMEOUT": "30"
      }
    }
  }
}
```

**For uv run from source:**
```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": ["--directory", "/path/to/fixed_schema_mcp_server", "run", "fastmcp_server.py"],
      "env": {
        "FASTMCP_LOG_LEVEL": "DEBUG",
        "AWS_DEFAULT_REGION": "us-west-2",
        "MCP_TIMEOUT": "30"
      }
    }
  }
}
```

### Logging Levels

Available logging levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (recommended)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only

## Alternative Configuration Methods

### Method 1: Direct Python Execution (from source)

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "python",
      "args": ["/path/to/your/fixed_schema_mcp_server/fastmcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/fixed_schema_mcp_server"
      }
    }
  }
}
```

### Method 2: Using pip/pipx Installation

This is the recommended approach for production use:

```bash
# Install once
pipx install fixed-schema-mcp-server

# Then use simple configuration
{
  "mcpServers": {
    "fixed-schema": {
      "command": "fixed-schema-mcp-server"
    }
  }
}
```

## Next Steps

1. **Test the integration** with simple queries
2. **Explore all available tools** to understand their capabilities
3. **Configure AWS Bedrock** for enhanced AI responses (optional)
4. **Customize schemas** for your specific use cases

For more information, see:
- [Main README](fixed_schema_mcp_server/README.md)
- [Kiro Integration Guide](fixed_schema_mcp_server/docs/kiro_integration.md)
- [Troubleshooting Guide](fixed_schema_mcp_server/docs/troubleshooting/README.md)