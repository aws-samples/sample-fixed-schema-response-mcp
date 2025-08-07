# JSON Schema MCP Server

A Model Context Protocol (MCP) server that dynamically loads JSON schemas and generates structured responses using FastMCP and AWS Bedrock Claude. This server automatically creates tools for any JSON schema you provide, making it completely extensible without code changes.

## Quick Start

1. **Run the server**:
   ```bash
   cd fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```

2. **Use in Kiro**:
   ```
   @fixed-schema get_product_info query: "iPhone 15 Pro"
   @fixed-schema get_recipe query: "chocolate chip cookies"
   @fixed-schema list_available_schemas
   ```

## Key Features

- **🔄 Dynamic Schema Loading**: Automatically loads all `.json` schema files
- **🛠️ Automatic Tool Generation**: Creates tools dynamically for each schema
- **🎯 Custom System Prompts**: Each schema can have specialized AI behavior
- **➕ Runtime Schema Addition**: Add new schemas without restarting
- **📋 Schema Discovery**: Built-in tools to list and explore available schemas

## Integration Guides

- **[Kiro Integration](fixed_schema_mcp_server/docs/KIRO_INTEGRATION.md)** - Complete setup guide for Kiro IDE
- **[Q Chat Integration](fixed_schema_mcp_server/docs/Q_CHAT_INTEGRATION.md)** - Complete setup guide for Q Chat
- **[Generic Usage Guide](fixed_schema_mcp_server/GENERIC_USAGE.md)** - How to use the generic architecture

## Documentation

For complete documentation, see: [`fixed_schema_mcp_server/README.md`](fixed_schema_mcp_server/README.md)

## Architecture

- **Generic & Extensible**: Add unlimited schemas without code changes
- **FastMCP Integration**: Built on the FastMCP framework
- **AWS Bedrock Integration**: Uses Claude for high-quality responses
- **Fallback Mechanism**: Provides mock responses when AWS credentials are not available
- **File-Driven**: All schemas loaded from JSON files in `test_config/schemas/`

## Current Available Tools

**Schema-Based Tools** (dynamically generated):
1. `get_api_endpoint`: API endpoint documentation
2. `get_article_summary`: Article summaries
3. `get_movie_review`: Movie reviews
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