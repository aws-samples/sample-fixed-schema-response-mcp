# Generic Schema MCP Server Usage Guide

The MCP server has been refactored to be completely generic and schema-driven. Instead of hardcoded tools for specific schemas, it now dynamically loads JSON schemas and creates corresponding tools automatically.

## Key Features

### 🔄 Dynamic Schema Loading
- Automatically loads all `.json` files from the `test_config/schemas/` directory
- Each schema file becomes a tool with the name `get_{schema_name}`
- No code changes needed to add new schemas

### 🛠️ Automatic Tool Generation
- Tools are created dynamically based on schema definitions
- Each tool accepts a `query` parameter and returns structured data
- Tool documentation is generated from schema descriptions

### 🎯 Custom System Prompts
- Each schema can include a custom `system_prompt` field
- Allows fine-tuning Claude's behavior for specific domains
- Falls back to generic prompt if not specified



## Schema File Format

Each schema file should follow this structure:

```json
{
  "name": "schema_name",
  "description": "Human-readable description of what this schema represents",
  "schema": {
    "type": "object",
    "required": ["field1", "field2"],
    "properties": {
      "field1": {
        "type": "string",
        "description": "Description of field1"
      },
      "field2": {
        "type": "number",
        "description": "Description of field2"
      }
    }
  },
  "system_prompt": "Optional custom system prompt for this schema"
}
```

## Available Tools

### Schema-Based Tools
For each schema file `{name}.json`, a tool `get_{name}` is automatically created:

- `get_product_info(query: str)` - Product information
- `get_person_profile(query: str)` - Person profiles  
- `get_api_endpoint(query: str)` - API documentation
- `get_troubleshooting_guide(query: str)` - Technical troubleshooting
- `get_article_summary(query: str)` - Article summaries
- `get_recipe(query: str)` - Cooking recipes

### Utility Tools
- `list_available_schemas()` - List all loaded schemas and their descriptions
- `add_schema(schema_name, schema_definition, description, system_prompt)` - Add new schema at runtime

## Adding New Schemas

### Method 1: File-based (Recommended)
1. Create a new `.json` file in `test_config/schemas/`
2. Follow the schema file format above
3. Restart the server to load the new schema

### Method 2: Runtime Addition (Requires Restart)
Use the `add_schema` tool to create schema files:

```python
add_schema(
    schema_name="book_review",
    schema_definition='{"type": "object", "properties": {"title": {"type": "string"}, "rating": {"type": "number"}}, "required": ["title"]}',
    description="Schema for book reviews",
    system_prompt="You are a literary critic providing book reviews."
)
```

**Note**: After using `add_schema`, you must restart the server for the new tool to become available.

## Example Usage

### Using a Schema Tool
```python
# Get recipe information
result = get_recipe("chocolate chip cookies")

# Get product information  
result = get_product_info("iPhone 15 Pro")

# Get troubleshooting help
result = get_troubleshooting_guide("WiFi connection issues")
```

### Listing Available Schemas
```python
schemas = list_available_schemas()
print(f"Available schemas: {schemas['total_count']}")
for name, info in schemas['available_schemas'].items():
    print(f"- {name}: {info['description']}")
```

## Configuration

The server loads configuration from `test_config/config.json`:

```json
{
    "schemas": {
        "path": "/path/to/schemas/directory",
        "default_schema": "product_info"
    },
    "model": {
        "provider": "bedrock",
        "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    }
}
```

## Benefits of the Generic Approach

1. **Scalability**: Add unlimited schemas without code changes
2. **Maintainability**: Single codebase handles all schema types
3. **Flexibility**: Custom system prompts per schema
4. **Discoverability**: Built-in schema listing and documentation
5. **Testing**: Generic mock response generation for all schemas
6. **Runtime Flexibility**: Add schemas dynamically without restarts

## Migration from Fixed Schema Version

The old hardcoded tools (`get_product_info`, etc.) are now automatically generated from schema files. The API remains the same, but the implementation is now completely generic and extensible.