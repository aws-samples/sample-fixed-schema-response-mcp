# Model Configuration Guide

The Fixed Schema MCP Server supports multiple AI model providers. This guide explains how to configure and use different providers.

## Supported Providers

### 1. AWS Bedrock (aws_bedrock)
- **Models**: Claude 3.5 Sonnet, Claude 3 Haiku, Titan Text Premier
- **Authentication**: AWS credentials (access keys, profiles, or IAM roles)
- **Region**: Configurable (default: us-west-2)

### 2. OpenAI (openai)
- **Models**: GPT-4o, GPT-4o-mini, GPT-4 Turbo, GPT-3.5 Turbo
- **Authentication**: API key
- **Base URL**: Configurable for custom endpoints

### 3. Anthropic (anthropic)
- **Models**: Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus
- **Authentication**: API key

### 4. Mock (mock)
- **Models**: Mock responses for testing
- **Authentication**: None required

## Configuration Methods

### Method 1: Using MCP Tools (Recommended)

The server provides built-in tools for configuration management:

#### Get Current Configuration
```
@fixed-schema get_model_config
```

#### Update Model Settings
```
@fixed-schema update_model_config provider="openai" model_id="gpt-4o" temperature=0.3
```

#### Update Credentials
```
@fixed-schema update_credentials provider="openai" api_key="your-api-key"
```

### Method 2: Direct Config File Editing

Edit `fixed_schema_mcp_server/test_config/config.json`:

```json
{
  "model": {
    "provider": "openai",
    "model_id": "gpt-4o",
    "parameters": {
      "temperature": 0.2,
      "top_p": 0.9,
      "max_tokens": 4096
    },
    "credentials": {
      "aws_region": "us-west-2"
    },
    "openai": {
      "api_key": "your-openai-api-key"
    },
    "anthropic": {
      "api_key": "your-anthropic-api-key"
    }
  }
}
```

## Provider-Specific Setup

### AWS Bedrock Setup

1. **Using AWS Profile** (Recommended):
   ```
   @fixed-schema update_credentials provider="aws_bedrock" profile_name="your-profile"
   ```

2. **Using Access Keys**:
   ```
   @fixed-schema update_credentials provider="aws_bedrock" aws_access_key_id="AKIA..." aws_secret_access_key="..." aws_region="us-west-2"
   ```

3. **Available Models**:
   - `us.anthropic.claude-3-7-sonnet-20250219-v1:0` (Latest Claude 3.5 Sonnet)
   - `us.anthropic.claude-3-5-sonnet-20241022-v2:0`
   - `us.anthropic.claude-3-haiku-20240307-v1:0`
   - `amazon.titan-text-premier-v1:0`

### OpenAI Setup

1. **Set API Key**:
   ```
   @fixed-schema update_credentials provider="openai" api_key="sk-..."
   ```

2. **Available Models**:
   - `gpt-4o` (Recommended)
   - `gpt-4o-mini`
   - `gpt-4-turbo`
   - `gpt-3.5-turbo`

### Anthropic Setup

1. **Set API Key**:
   ```
   @fixed-schema update_credentials provider="anthropic" api_key="sk-ant-..."
   ```

2. **Available Models**:
   - `claude-3-5-sonnet-20241022` (Recommended)
   - `claude-3-5-haiku-20241022`
   - `claude-3-opus-20240229`

## Environment Variables

You can also set credentials using environment variables:

- **OpenAI**: `OPENAI_API_KEY`
- **Anthropic**: `ANTHROPIC_API_KEY`
- **AWS**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`

## Testing Configuration

After updating configuration, restart the MCP server and test with any schema tool:

```
@fixed-schema get_weather_report query="Weather in San Francisco"
```

The server will automatically fall back to mock responses if the configured provider is unavailable.

## Troubleshooting

### Common Issues

1. **"Client not available"**: Check credentials and restart server
2. **"Unknown model type"**: Verify model ID matches available models
3. **API errors**: Check API key validity and rate limits
4. **AWS region errors**: Ensure model is available in your region

### Debug Logging

The server logs detailed information about model invocations. Check logs for:
- Provider initialization status
- API call success/failure
- Response parsing issues
- Fallback to mock responses

### Fallback Behavior

The server gracefully handles failures:
1. Invalid credentials → Mock responses
2. API errors → Mock responses  
3. Network issues → Mock responses
4. Unknown models → Mock responses

This ensures the server remains functional even with configuration issues.