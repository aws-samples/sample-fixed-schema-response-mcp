# Fixed Schema MCP Server

A Model Context Protocol (MCP) server that dynamically loads JSON schemas and generates structured responses using FastMCP. Simply add a JSON schema file and get a corresponding tool instantly—no code changes required.

## Key Features

- **Dynamic Schema Loading**: Automatically loads all JSON schema files from the config directory
- **Automatic Tool Generation**: Each schema becomes a tool named `get_{schema_name}` without any coding
- **Multi-Provider AI Support**: Works with AWS Bedrock, OpenAI, Anthropic, or mock responses
- **Schema Management**: Built-in tools to list, add, and delete schemas at runtime
- **Flexible Credentials**: Supports local environment variables or MCP configuration
- **Zero Code Changes**: Add unlimited schemas without modifying server code
- **Custom System Prompts**: Each schema can include specialized AI behavior instructions

## Installation

### Using pip

```bash
# Install from source
pip install .

# Install with optional AI provider dependencies
pip install .[openai]
pip install .[anthropic]
pip install .[all]
```

### Using pipx (Isolated Environment)

```bash
# Install from source
pipx install .

# Install from git repository
pipx install git+https://github.com/yourusername/fixed-schema-mcp-server.git
```

### Using uv (Development)

```bash
cd fixed_schema_mcp_server
uv run fastmcp_server.py
```

## Quick Start

1. **Install the server** (choose one method above)

2. **Configure credentials** (optional for AWS Bedrock):
   ```bash
   export AWS_PROFILE="your-profile"
   export OPENAI_API_KEY="sk-proj-your-key"
   ```

3. **Run the server**:
   ```bash
   # If installed via pip/pipx
   fixed-schema-mcp-server
   
   # Or using uv for development
   cd fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```

4. **Test with MCP client**:
   ```
   @fixed-schema list_available_schemas
   @fixed-schema get_weather_report query: "Weather in San Francisco"
   @fixed-schema get_product_info query: "iPhone 15 Pro"
   ```

## Basic Usage

### List Available Schemas

```
@fixed-schema list_available_schemas
```

### Use Schema-Based Tools

All schema-based tools accept a `query` parameter:

```
@fixed-schema get_recipe query: "chocolate chip cookies"
@fixed-schema get_person_profile query: "Elon Musk"
@fixed-schema get_troubleshooting_guide query: "computer won't start"
```

### Add a New Schema

```
@fixed-schema add_schema schema_name: "book_review" schema_definition: "{...}" description: "Book review schema"
```

### Delete a Schema

```
@fixed-schema delete_schema schema_name: "old_schema"
```

## Documentation

- **[Complete Usage Guide](fixed_schema_mcp_server/README.md)** - Detailed documentation with all tools and examples
- **[Adding Schemas Guide](fixed_schema_mcp_server/docs/ADDING_SCHEMAS.md)** - How to create custom schemas
- **[Kiro Integration](fixed_schema_mcp_server/docs/kiro_integration.md)** - Setup guide for Kiro IDE
- **[Q Chat Integration](fixed_schema_mcp_server/docs/Q_CHAT_INTEGRATION.md)** - Setup guide for Q Chat
- **[MCP Credentials Setup](fixed_schema_mcp_server/docs/MCP_CREDENTIALS_SETUP.md)** - Configure AI provider credentials
- **[Security Best Practices](fixed_schema_mcp_server/docs/SECURITY_BEST_PRACTICES.md)** - Security guidelines

## License

This project is licensed under the MIT License.