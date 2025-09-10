# MCP Credentials Setup Guide

This guide shows how to configure AI provider credentials directly in your MCP configuration file (`.kiro/settings/mcp.json`). This is the recommended approach as it keeps all configuration in one place.

## Quick Setup Examples

### AWS Bedrock with Access Keys (Recommended)
```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/fixed_schema_mcp_server", "fastmcp_server.py"],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "AWS_ACCESS_KEY_ID": "<AWS ACCESS KEY ID>",
        "AWS_SECRET_ACCESS_KEY": "<AWS SECRET ACCESS KEY>",
        "AWS_SESSION_TOKEN": "<AWS SESSION TOKEN>",
        "AWS_REGION": "us-west-2"
      }
    }
  }
}
```

### AWS Bedrock with Profile (Alternative)
```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/fixed_schema_mcp_server", "fastmcp_server.py"],
      "env": {
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-west-2"
      }
    }
  }
}
```

### OpenAI Setup
```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/fixed_schema_mcp_server", "fastmcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-proj-your-openai-key"
      }
    }
  }
}
```

### Anthropic Setup
```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/fixed_schema_mcp_server", "fastmcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-your-anthropic-key"
      }
    }
  }
}
```

## Switching Between Providers

Once you have credentials configured, you can switch providers using the built-in tools:

1. **Check current configuration**:
   ```
   @fixed-schema get_model_config
   ```

2. **Switch to OpenAI**:
   ```
   @fixed-schema update_model_config provider="openai" model_id="gpt-4o"
   ```

3. **Switch to Anthropic**:
   ```
   @fixed-schema update_model_config provider="anthropic" model_id="claude-3-5-sonnet-20241022"
   ```

4. **Switch to AWS Bedrock**:
   ```
   @fixed-schema update_model_config provider="aws_bedrock" model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
   ```

## Complete Multi-Provider Setup

Here's a complete configuration that supports all providers:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/username/fixed_schema_mcp_server",
        "fastmcp_server.py"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "AWS_ACCESS_KEY_ID": "<AWS ACCESS KEY ID>",
        "AWS_SECRET_ACCESS_KEY": "<AWS SECRET ACCESS KEY>",
        "AWS_SESSION_TOKEN": "<AWS SESSION TOKEN>",
        "AWS_REGION": "us-west-2",
        "OPENAI_API_KEY": "sk-proj-your-openai-key",
        "OPENAI_ORGANIZATION": "org-your-org-id",
        "ANTHROPIC_API_KEY": "sk-ant-your-anthropic-key"
      },
      "disabled": false,
      "autoApprove": [
        "list_available_schemas",
        "get_model_config",
        "update_model_config",
        "get_weather_report",
        "get_recipe",
        "get_product_info"
      ]
    }
  }
}
```

## Environment Variables Reference

### AWS Bedrock
- `AWS_ACCESS_KEY_ID`: AWS access key (recommended for MCP)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (recommended for MCP)
- `AWS_SESSION_TOKEN`: AWS session token (for temporary credentials)
- `AWS_REGION` or `AWS_DEFAULT_REGION`: AWS region
- `AWS_PROFILE`: AWS profile name (alternative approach)

### OpenAI
- `OPENAI_API_KEY`: OpenAI API key (required)
- `OPENAI_BASE_URL`: Custom API endpoint (optional)
- `OPENAI_ORGANIZATION`: Organization ID (optional)

### Anthropic
- `ANTHROPIC_API_KEY`: Anthropic API key (required)

## Security Best Practices

1. **Use Temporary Credentials**: Use AWS STS temporary credentials when possible
2. **Rotate API Keys**: Regularly rotate your API keys and access keys
3. **Limit Permissions**: Use least-privilege access for AWS credentials
4. **Environment Isolation**: Use different credentials for different environments
5. **Secure Storage**: Keep credentials secure and never commit them to version control

## Available Models by Provider

### AWS Bedrock
- `us.anthropic.claude-3-7-sonnet-20250219-v1:0` (Latest Claude 3.5 Sonnet)
- `us.anthropic.claude-3-5-sonnet-20241022-v2:0`
- `us.anthropic.claude-3-haiku-20240307-v1:0`
- `amazon.titan-text-premier-v1:0`

### OpenAI
- `gpt-4o` (Recommended)
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### Anthropic
- `claude-3-5-sonnet-20241022` (Recommended)
- `claude-3-5-haiku-20241022`
- `claude-3-opus-20240229`

## Troubleshooting

### Check Configuration Status
```
@fixed-schema get_model_config
```

**Example Response:**
```json
{
  "current_config": {
    "provider": "aws_bedrock",
    "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "credentials_configured": {
      "aws_bedrock": true,
      "openai": false,
      "anthropic": false
    }
  },
  "available_providers": {
    "aws_bedrock": {
      "models": ["us.anthropic.claude-3-7-sonnet-20250219-v1:0", "..."]
    }
  }
}
```

This shows:
- Current provider and model
- Which credentials are configured
- Available providers and models

### Common Issues

1. **"Client not available"**: 
   - Check that the API key/credentials are set correctly in MCP config
   - Verify the environment variable names match exactly

2. **AWS region errors**:
   - Ensure the model is available in your specified region
   - Try `us-west-2` or `us-east-1` for best model availability

3. **Import errors**:
   - Install required packages: `uv add openai anthropic`

### Debug Mode

Enable debug logging to see credential loading details:

```json
"env": {
  "FASTMCP_LOG_LEVEL": "DEBUG"
}
```

## Example Workflow

1. **Set up credentials** in `.kiro/settings/mcp.json`
2. **Restart the MCP server** (or reconnect in Kiro)
3. **Discover available tools**: `@fixed-schema list_available_schemas`
4. **Check configuration**: `@fixed-schema get_model_config`
5. **Test with a schema**: `@fixed-schema get_weather_report query="Weather in Tokyo"`
6. **Switch providers** as needed: `@fixed-schema update_model_config provider="openai" model_id="gpt-4o"`
7. **Use any of the 12+ schema tools**: `@fixed-schema get_recipe query="chocolate cake"`

## Testing Your Setup

### 1. List Available Schemas
```
@fixed-schema list_available_schemas
```
**Expected Result**: Shows all 12 available schema tools with descriptions.

### 2. Check Model Configuration
```
@fixed-schema get_model_config
```
**Expected Result**: Shows current provider, available credentials, and model options.

### 3. Test a Schema Tool
```
@fixed-schema get_weather_report query="Weather in San Francisco"
```
**Expected Result**: Returns structured weather data (mock data if no AI provider configured).

### 4. Switch Providers (if multiple configured)
```
@fixed-schema update_model_config provider="openai" model_id="gpt-4o"
```
**Expected Result**: Successfully updates configuration for next restart.

## Verified Working Configuration

✅ **Tested and Working** (as of latest test):
- **12 Schema Tools**: All dynamically generated and functional
  - `api_endpoint`, `article_summary`, `book_review`, `movie_review`
  - `person_profile`, `product_info`, `recipe`, `sports_stats`
  - `troubleshooting_guide`, `user_profile_test`, `weather_report`, `test@schema`
- **AWS Bedrock**: Working with AWS profile credentials
- **Provider Switching**: Seamless switching between providers
- **Mock Fallback**: Graceful fallback when providers unavailable
- **Auto-Approval**: Key tools auto-approved in Kiro for smooth workflow

The server will automatically use the configured credentials and fall back to mock responses if the selected provider is unavailable.