# Changelog

## [2.0.0] - 2025-08-09

### Added - Multi-Provider Model Support

#### New Features
- **Multi-Provider Support**: Added support for AWS Bedrock, OpenAI, Anthropic, and Mock providers
- **Runtime Configuration**: Configure model providers and credentials without code changes
- **Credential Management**: Secure credential storage and management for all providers
- **Graceful Fallback**: Automatic fallback to mock responses when providers are unavailable

#### New MCP Tools
- `get_model_config`: Get current model configuration and available providers
- `update_model_config`: Update model provider, model ID, and parameters
- `update_credentials`: Update credentials for specific providers

#### Supported Models
- **AWS Bedrock**: Claude 3.5 Sonnet, Claude 3 Haiku, Titan Text Premier
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4 Turbo, GPT-3.5 Turbo  
- **Anthropic**: Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus
- **Mock**: Testing and fallback responses

#### Configuration Methods
- **MCP Tools**: Use built-in tools for runtime configuration
- **Config File**: Direct editing of `config/config.json`
- **Environment Variables**: Support for standard environment variables

#### Documentation
- **[Model Configuration Guide](docs/MODEL_CONFIGURATION.md)**: Complete setup guide for all providers
- **Updated Architecture**: Multi-provider architecture with graceful fallback
- **Provider-Specific Setup**: Detailed instructions for each provider

### Enhanced
- **Error Handling**: Improved error handling with automatic fallback to mock responses
- **Logging**: Enhanced logging for model invocations and provider status
- **Dependencies**: Added optional dependencies for OpenAI and Anthropic clients

### Technical Changes
- Refactored `invoke_claude` to `invoke_model` with provider routing
- Added provider-specific invocation functions
- Enhanced configuration loading with credential management
- Added JSON extraction utilities for consistent response parsing

### Backward Compatibility
- Existing schemas and tools continue to work unchanged
- Default configuration maintains AWS Bedrock compatibility
- Mock responses ensure functionality without credentials

### Migration Guide
- No breaking changes for existing users
- New configuration options are optional
- Server automatically detects and uses available credentials
- Existing AWS Bedrock setups continue to work without changes