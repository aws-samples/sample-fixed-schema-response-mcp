# JSON Schema MCP Server

A Model Context Protocol (MCP) server that dynamically loads JSON schemas and generates structured responses using FastMCP and AWS Bedrock Claude. This server automatically creates tools for any JSON schema you provide, making it completely extensible without code changes.

## Quick Start

1. **Run the server**:
   ```bash
   cd fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```

2. **Configure credentials** (multiple options):

   **Option A: User your local creds**:
   ```bash
   # If you already have AWS CLI configured or environment variables set
   export AWS_PROFILE="your-profile"
   export OPENAI_API_KEY="sk-proj-your-key"
   ```
   
   **Option B: Set in MCP config** (`.kiro/settings/mcp.json`):
   ```json
   {
     "mcpServers": {
       "fixed-schema": {
         "env": {
           "AWS_ACCESS_KEY_ID": "<AWS ACCESS KEY ID>",
           "AWS_SECRET_ACCESS_KEY": "<AWS SECRET ACCESS KEY>",
           "AWS_REGION": "us-west-2",
           "OPENAI_API_KEY": "sk-proj-your-key"
         }
       }
     }
   }
   ```

3. **Test the server**:
   ```
   @fixed-schema list_available_schemas
   @fixed-schema get_model_config
   @fixed-schema get_weather_report query: "Weather in San Francisco"
   ```
   
   The server automatically detects your local AWS credentials and API keys!

4. **Switch providers and use schemas**:
   ```
   @fixed-schema update_model_config provider="openai" model_id="gpt-4o"
   @fixed-schema get_product_info query: "iPhone 15 Pro"
   @fixed-schema get_recipe query: "chocolate chip cookies"
   @fixed-schema get_troubleshooting_guide query: "WiFi connection issues"
   ```

## Key Features

- **🔄 Dynamic Schema Loading**: Automatically loads all `.json` schema files
- **🛠️ Automatic Tool Generation**: Creates tools dynamically for each schema
- **🎯 Custom System Prompts**: Each schema can have specialized AI behavior
- **📋 Schema Discovery**: Built-in tools to list and explore available schemas
- **🤖 Multi-Provider Support**: AWS Bedrock, OpenAI, Anthropic, or Mock responses
- **🔑 Flexible Credentials**: Reads from local environment or MCP config
- **⚙️ Runtime Configuration**: Update model settings and credentials without code changes

## Integration Guides

- **[MCP Credentials Setup](fixed_schema_mcp_server/docs/MCP_CREDENTIALS_SETUP.md)** - Configure AI provider credentials in MCP config
- **[Kiro Integration](fixed_schema_mcp_server/docs/KIRO_INTEGRATION.md)** - Complete setup guide for Kiro IDE
- **[Q Chat Integration](fixed_schema_mcp_server/docs/Q_CHAT_INTEGRATION.md)** - Complete setup guide for Q Chat
- **[Generic Usage Guide](fixed_schema_mcp_server/GENERIC_USAGE.md)** - How to use the generic architecture

## Documentation

For complete documentation, see: [`fixed_schema_mcp_server/README.md`](fixed_schema_mcp_server/README.md)

## Architecture

- **Generic & Extensible**: Add unlimited schemas without code changes
- **FastMCP Integration**: Built on the FastMCP framework
- **Multi-Provider AI**: AWS Bedrock, OpenAI, Anthropic, or Mock responses
- **Smart Credential Loading**: Reads from local environment variables or MCP config
- **Graceful Fallback**: Automatic fallback to mock responses when providers unavailable
- **File-Driven**: All schemas loaded from JSON files in `test_config/schemas/`
- **Runtime Configuration**: Update settings via MCP tools without server code changes

## Current Available Tools (12 Schema-Based Tools)

**Schema-Based Tools** (dynamically generated from JSON files):
1. `get_api_endpoint`: API endpoint documentation
2. `get_article_summary`: Article summary responses
3. `get_book_review`: Book review information
4. `get_movie_review`: Movie review information
5. `get_person_profile`: Structured person information
6. `get_product_info`: Product information responses
7. `get_recipe`: Cooking recipe information
8. `get_sports_stats`: Sports statistics information
9. `get_troubleshooting_guide`: Technical troubleshooting guides
10. `get_user_profile_test`: User profile test schema
11. `get_weather_report`: Weather report information
12. `get_test@schema`: Test schema with special characters

**Configuration Tools**:
- `list_available_schemas`: Discover all available schema tools
- `get_model_config`: View current model configuration and credentials
- `update_model_config`: Switch between AI providers and models
- `add_schema`: Add new schemas dynamically
4. `get_person_profile`: Person profiles
5. `get_product_info`: Product information
6. `get_recipe`: Cooking recipes
7. `get_troubleshooting_guide`: Technical troubleshooting

**Utility Tools**:
- `list_available_schemas`: Discover all available schemas
- `add_schema`: Add new schemas at runtime

## Adding New Schemas

Simply drop a JSON schema file in `test_config/schemas/` and restart:

```json
{
  "name": "book_review",
  "description": "Schema for book reviews",
  "schema": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "rating": {"type": "number"}
    },
    "required": ["title", "rating"]
  },
  "system_prompt": "You are a literary critic..."
}
```

The tool `get_book_review` will be automatically available!

## License

This project is licensed under the MIT License.