# Kiro Integration Guide

This guide explains how to integrate the Fixed Schema Response MCP Server with Kiro IDE.

## Prerequisites

- Kiro IDE installed and running
- `uv` package manager installed ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- Python 3.10 or higher
- Fixed Schema MCP Server downloaded/cloned

## Step-by-Step Setup

### 1. Get Your Absolute Path

First, navigate to your project directory and get the absolute path:

```bash
cd fixed_schema_mcp_server
pwd  # Copy this path for the next step
```

Example output: `/Users/fanhongy/Project/mcps-proj/fixed_schema_mcp_server`

### 2. Configure Kiro MCP Settings

Open Kiro and configure the MCP server. You can do this by:

**Option A: Edit the configuration file directly**
- Open `.kiro/settings/mcp.json` in your project
- Add the fixed-schema server configuration

**Option B: Use Kiro's interface**
- Use the command palette (Cmd/Ctrl + Shift + P)
- Search for "MCP" settings
- Add a new MCP server

### 3. Add Server Configuration

Add this configuration to your `.kiro/settings/mcp.json`:

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
    }
  }
}
```

**Important**: Replace the path in `--directory` with your actual absolute path from step 1.

### 4. Test the Connection

After saving the configuration:

1. **Restart Kiro** (if needed)
2. **Check MCP server status** in Kiro's interface
3. **Look for "fixed-schema"** in the available MCP servers list
4. **Test with a simple command** in a Kiro chat

## Using Tools in Kiro

Once configured, you can use the tools directly in Kiro conversations:

### Product Information
Get structured information about products with pricing, features, and availability:

```
@fixed-schema get_product_info product_name: "MacBook Pro M3"
```

**Response format:**
```json
{
  "name": "MacBook Pro M3",
  "description": "Apple's latest professional laptop...",
  "price": 1999.99,
  "category": "Laptops",
  "features": ["M3 chip", "16GB RAM", "512GB SSD"],
  "rating": 4.8,
  "inStock": true
}
```

### Person Profiles  
Get structured biographical information about people:

```
@fixed-schema get_person_profile person_name: "Tim Cook"
```

**Response format:**
```json
{
  "name": "Tim Cook",
  "age": 63,
  "occupation": "CEO of Apple Inc.",
  "skills": ["Leadership", "Operations", "Strategy"],
  "contact": {
    "email": "tim.cook@example.com",
    "phone": "555-123-4567"
  }
}
```

### API Documentation
Get structured API endpoint documentation:

```
@fixed-schema get_api_endpoint endpoint_name: "payment processing"
```

**Response format:**
```json
{
  "path": "/api/v1/payment-processing",
  "method": "POST",
  "description": "Process payment transactions",
  "parameters": [
    {
      "name": "amount",
      "type": "number",
      "required": true,
      "description": "Payment amount"
    }
  ],
  "responses": [
    {
      "code": 200,
      "description": "Payment successful",
      "example": {"status": "success", "transaction_id": "12345"}
    }
  ]
}
```

### Troubleshooting Guides
Get step-by-step troubleshooting guides:

```
@fixed-schema get_troubleshooting_guide issue: "Docker container won't start"
```

**Response format:**
```json
{
  "issue": "Problem with Docker container won't start",
  "symptoms": [
    "Container fails to start",
    "Error messages in logs",
    "Port conflicts"
  ],
  "causes": [
    "Port already in use",
    "Insufficient resources",
    "Configuration errors"
  ],
  "solutions": [
    {
      "step": 1,
      "description": "Check if port is already in use: docker ps"
    },
    {
      "step": 2,
      "description": "Stop conflicting containers"
    },
    {
      "step": 3,
      "description": "Restart Docker service"
    }
  ],
  "preventionTips": [
    "Use unique port mappings",
    "Monitor resource usage"
  ]
}
```

### Article Summaries
Get structured summaries of articles or topics:

```
@fixed-schema get_article_summary topic: "machine learning trends 2024"
```

**Response format:**
```json
{
  "title": "Machine Learning Trends 2024",
  "author": "AI Assistant",
  "date": "2024-07-24",
  "summary": "Overview of key machine learning developments in 2024...",
  "keyPoints": [
    "Large Language Models continue to evolve",
    "Edge AI deployment increases",
    "Multimodal AI becomes mainstream"
  ],
  "conclusion": "2024 marks a significant year for practical AI applications"
}
```

## Kiro-Specific Features

### Auto-Approval
The `autoApprove` list in the configuration means Kiro will automatically execute these tools without asking for permission each time. This provides a smoother user experience.

### Environment Variables
You can add custom environment variables for AWS configuration:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": ["--directory", "/path/to/fixed_schema_mcp_server", "run", "fastmcp_server.py"],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "your-key-id",
        "AWS_SECRET_ACCESS_KEY": "your-secret-key"
      }
    }
  }
}
```

### Steering Files
Create a steering file at `.kiro/steering/fixed-schema-mcp.md` to provide context about the MCP server:

```markdown
---
inclusion: manual
---

# Fixed Schema Response MCP Server

This MCP server provides structured responses for:
- Product information with pricing and features
- Person profiles with professional details  
- API endpoint documentation
- Technical troubleshooting guides
- Article summaries with key points

## Usage Examples

- `@fixed-schema get_product_info product_name: "iPhone 15"`
- `@fixed-schema get_person_profile person_name: "Satya Nadella"`
- `@fixed-schema get_api_endpoint endpoint_name: "user authentication"`
- `@fixed-schema get_troubleshooting_guide issue: "server not responding"`
- `@fixed-schema get_article_summary topic: "cloud computing"`

## Tips

- Be specific in your queries for better results
- The server uses AWS Bedrock Claude when available, falls back to mock responses
- All responses follow predefined JSON schemas for consistency
```

## Troubleshooting

### Server Not Connecting

**Symptoms:**
- Error message: "Failed to connect to MCP server"
- No response from the server
- Server not appearing in Kiro's MCP list

**Solutions:**

1. **Check the absolute path**:
   ```bash
   ls -la /your/absolute/path/to/fixed_schema_mcp_server/fastmcp_server.py
   ```

2. **Verify uv installation**:
   ```bash
   which uv
   uv --version
   ```

3. **Test the server manually**:
   ```bash
   cd fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```

4. **Check Kiro's MCP logs** for detailed error messages

### Tools Not Available

**Symptoms:**
- `@fixed-schema` commands not recognized
- Tools don't appear in Kiro's tool list
- "Tool not found" errors

**Solutions:**

1. **Check MCP server status** in Kiro's interface
2. **Restart Kiro** after configuration changes
3. **Verify autoApprove list** includes the tools you want to use
4. **Check for typos** in tool names

### Dependency Issues

**Symptoms:**
- Error about missing `fastmcp`, `boto3`, or other dependencies
- Import errors in logs

**Solutions:**

1. **Test uv dependency resolution**:
   ```bash
   cd fixed_schema_mcp_server
   uv run --help
   ```

2. **Check Python version**:
   ```bash
   python --version  # Should be 3.10+
   ```

3. **Clear uv cache** if needed:
   ```bash
   uv cache clean
   ```

### AWS Bedrock Issues

**Symptoms:**
- Getting generic/mock responses instead of detailed AI-generated content
- Warning messages about AWS credentials

**Solutions:**

1. **Configure AWS credentials**:
   ```bash
   aws configure
   ```

2. **Set environment variables** in the MCP configuration:
   ```json
   {
     "env": {
       "AWS_ACCESS_KEY_ID": "your-key",
       "AWS_SECRET_ACCESS_KEY": "your-secret",
       "AWS_DEFAULT_REGION": "us-east-1"
     }
   }
   ```

3. **Note**: The server automatically falls back to mock responses if AWS is unavailable - this is normal behavior for testing.

## Advanced Configuration

### Multiple Environments

You can configure different environments for development and production:

```json
{
  "mcpServers": {
    "fixed-schema-dev": {
      "command": "uv",
      "args": ["--directory", "/path/to/dev/fixed_schema_mcp_server", "run", "fastmcp_server.py"],
      "env": {"FASTMCP_LOG_LEVEL": "DEBUG"},
      "autoApprove": ["get_product_info"]
    },
    "fixed-schema-prod": {
      "command": "uv", 
      "args": ["--directory", "/path/to/prod/fixed_schema_mcp_server", "run", "fastmcp_server.py"],
      "env": {"FASTMCP_LOG_LEVEL": "ERROR"},
      "autoApprove": ["get_product_info", "get_person_profile", "get_api_endpoint"]
    }
  }
}
```

### Logging Levels

Configure different logging levels based on your needs:

- `DEBUG`: Detailed debugging information (verbose)
- `INFO`: General information (recommended for development)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only (recommended for production)

### Custom Schemas

You can extend the server with custom schemas by:

1. Adding new schema files to `test_config/schemas/`
2. Adding corresponding tool functions to `fastmcp_server.py`
3. Including the new tools in the `autoApprove` list

## Performance Tips

1. **Use specific queries** for better response quality
2. **Configure AWS Bedrock** for enhanced AI responses (optional)
3. **Monitor logs** to identify any performance issues
4. **Use appropriate logging levels** to reduce noise

## Next Steps

1. **Test all available tools** to understand their capabilities
2. **Configure AWS Bedrock** for enhanced AI responses (optional)
3. **Create custom steering files** for your specific use cases
4. **Explore schema customization** for specialized needs

For more information, see:
- [Main README](README.md)
- [Q Chat Integration Guide](Q_CHAT_INTEGRATION.md)
- [Detailed Documentation](fixed_schema_mcp_server/README.md)