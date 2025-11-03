# Adding New Schemas Guide

This guide explains how to add custom schemas to the Generic Schema MCP Server. With the new architecture, adding schemas is incredibly simple - just drop a JSON file and restart!

## Overview

The Generic MCP server automatically loads JSON schemas and creates corresponding tools. Each schema consists of:
1. **Schema Definition** - JSON file defining the response structure (this is all you need!)
2. **Automatic Tool Generation** - The server creates tools automatically
3. **Optional Configuration** - Add the tool to MCP client autoApprove lists

**No code changes required!** The server handles everything automatically.

## Simple Step-by-Step Process

### Step 1: Create a Schema File (That's It!)

Create a new JSON file in the `fixed_schema_mcp_server/config/schemas/` directory.

**Example: Creating a `book_review.json` schema**

```bash
cd fixed_schema_mcp_server/config/schemas
```

Create `book_review.json`:

```json
{
  "name": "book_review",
  "description": "Schema for book review information",
  "schema": {
    "type": "object",
    "required": ["title", "author", "rating", "review"],
    "properties": {
      "title": {
        "type": "string",
        "description": "The title of the book"
      },
      "author": {
        "type": "string", 
        "description": "The author of the book"
      },
      "isbn": {
        "type": "string",
        "description": "The ISBN of the book"
      },
      "rating": {
        "type": "number",
        "minimum": 1,
        "maximum": 5,
        "description": "Rating from 1 to 5 stars"
      },
      "review": {
        "type": "string",
        "description": "Detailed review of the book"
      },
      "genres": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "List of genres the book belongs to"
      },
      "publication_year": {
        "type": "integer",
        "description": "Year the book was published"
      },
      "recommended": {
        "type": "boolean",
        "description": "Whether the book is recommended"
      },
      "similar_books": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "List of similar book recommendations"
      }
    }
  },
  "system_prompt": "You are a professional book critic with expertise in literature. Provide thoughtful, balanced book reviews that consider plot, character development, writing style, and overall literary merit."
}
```

### Step 2: Restart the Server

That's it! Just restart the MCP server:

```bash
cd fixed_schema_mcp_server
uv run fastmcp_server.py
```

The tool `get_book_review` is now automatically available!

### Step 3: Update MCP Client Configurations (Optional)

#### For Kiro (`.kiro/settings/mcp.json`):

Add the new tool to the `autoApprove` list:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": ["--directory", "/path/to/fixed_schema_mcp_server", "run", "fastmcp_server.py"],
      "autoApprove": [
        "get_product_info",
        "get_article_summary",
        "get_person_profile", 
        "get_api_endpoint",
        "get_troubleshooting_guide",
        "get_book_review"
      ]
    }
  }
}
```

#### For Q Chat:

Add the new tool to your Q Chat MCP configuration's `autoApprove` list similarly.

### Step 4: Test Your New Schema

1. **Verify the schema loaded**:
   ```bash
   cd fixed_schema_mcp_server
   python -c "import fastmcp_server; print('book_review' in fastmcp_server.SCHEMAS)"
   ```

2. **Test in Kiro**:
   ```
   @fixed-schema get_book_review query: "The Great Gatsby by F. Scott Fitzgerald"
   ```

3. **List all schemas to confirm**:
   ```
   @fixed-schema list_available_schemas
   ```

## Schema Design Best Practices

### 1. Required vs Optional Fields

Mark essential fields as required:

```json
{
  "required": ["title", "author", "rating"],
  "properties": {
    "title": {"type": "string"},
    "author": {"type": "string"},
    "rating": {"type": "number"},
    "isbn": {"type": "string"}  // Optional
  }
}
```

### 2. Use Appropriate Data Types

Choose the right JSON Schema types:

```json
{
  "properties": {
    "title": {"type": "string"},
    "rating": {"type": "number", "minimum": 1, "maximum": 5},
    "page_count": {"type": "integer"},
    "is_bestseller": {"type": "boolean"},
    "genres": {"type": "array", "items": {"type": "string"}},
    "metadata": {"type": "object"}
  }
}
```

### 3. Add Validation Constraints

Use JSON Schema validation features:

```json
{
  "properties": {
    "email": {
      "type": "string",
      "format": "email"
    },
    "rating": {
      "type": "number",
      "minimum": 1,
      "maximum": 5
    },
    "isbn": {
      "type": "string",
      "pattern": "^978-\\d{1,5}-\\d{1,7}-\\d{1,7}-\\d{1}$"
    },
    "description": {
      "type": "string",
      "minLength": 10,
      "maxLength": 1000
    }
  }
}
```

### 4. Provide Clear Descriptions

Add descriptions for better AI understanding:

```json
{
  "properties": {
    "sentiment": {
      "type": "string",
      "enum": ["positive", "negative", "neutral"],
      "description": "Overall sentiment of the review"
    },
    "themes": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Main themes explored in the book"
    }
  }
}
```

## Complex Schema Examples

### Nested Objects

```json
{
  "name": "restaurant_review",
  "schema": {
    "type": "object",
    "properties": {
      "restaurant": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "cuisine": {"type": "string"},
          "location": {
            "type": "object",
            "properties": {
              "address": {"type": "string"},
              "city": {"type": "string"},
              "coordinates": {
                "type": "object",
                "properties": {
                  "lat": {"type": "number"},
                  "lng": {"type": "number"}
                }
              }
            }
          }
        }
      },
      "review": {
        "type": "object",
        "properties": {
          "rating": {"type": "number", "minimum": 1, "maximum": 5},
          "food_quality": {"type": "number", "minimum": 1, "maximum": 5},
          "service": {"type": "number", "minimum": 1, "maximum": 5},
          "atmosphere": {"type": "number", "minimum": 1, "maximum": 5},
          "comments": {"type": "string"}
        }
      }
    }
  }
}
```

### Arrays of Objects

```json
{
  "name": "movie_cast",
  "schema": {
    "type": "object",
    "properties": {
      "movie_title": {"type": "string"},
      "cast": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "actor_name": {"type": "string"},
            "character_name": {"type": "string"},
            "role_type": {
              "type": "string",
              "enum": ["lead", "supporting", "cameo"]
            }
          }
        }
      }
    }
  }
}
```

## How the Generic Architecture Works

### Automatic Tool Generation

The server automatically creates tools for each schema file:

1. **File Discovery**: Scans `config/schemas/*.json` files
2. **Schema Loading**: Loads each JSON schema definition
3. **Tool Creation**: Creates a function named `get_{schema_name}`
4. **Tool Registration**: Registers the tool with the MCP framework

### Generated Tool Pattern

Each generated tool follows this pattern:

```python
def get_{schema_name}(query: str) -> Dict[str, Any]:
    """
    {schema.description}
    
    Args:
        query: The input query or request
    
    Returns:
        {schema_name} information in a structured format
    """
    # Uses schema description to create specific prompt
    prompt = f"Please provide {schema.description} based on this query: {query}"
    
    # Uses custom system prompt if available
    return invoke_claude(prompt, schema_name)
```

### Benefits of the Generic Approach

- **No Code Changes**: Add schemas without touching Python code
- **Consistent Interface**: All tools use the same `query` parameter
- **Automatic Documentation**: Tool descriptions generated from schema metadata
- **Custom AI Behavior**: Each schema can have its own system prompt
- **Mock Response Generation**: Automatic fallback responses based on schema structure

## Testing Your Schema

### 1. Schema Validation Test

Create a test to validate your schema works:

```python
# Add to test_schemas.py or create a new test file
import json
import jsonschema

def test_book_review_schema():
    # Load your schema
    with open('config/schemas/book_review.json', 'r') as f:
        schema_def = json.load(f)
    
    # Test valid data
    valid_data = {
        "title": "Test Book",
        "author": "Test Author", 
        "rating": 4.5,
        "review": "Great book!"
    }
    
    # This should not raise an exception
    jsonschema.validate(valid_data, schema_def['schema'])
    print("Schema validation passed!")

if __name__ == "__main__":
    test_book_review_schema()
```

### 2. Integration Test

Test the complete flow:

```bash
cd fixed_schema_mcp_server

# Test the server starts
uv run fastmcp_server.py &
SERVER_PID=$!

# Test in Kiro or Q Chat
# @fixed-schema get_book_review book_title: "1984" author: "George Orwell"

# Clean up
kill $SERVER_PID
```

## Common Issues and Solutions

### Issue: Schema Not Loading

**Symptoms:**
- Error: "Unknown schema: your_schema_name"
- Schema not found in logs

**Solutions:**
1. Check file name matches schema name
2. Verify JSON syntax is valid
3. Restart the server after adding schema
4. Check file permissions

### Issue: Validation Failures

**Symptoms:**
- Responses don't match expected format
- Missing required fields

**Solutions:**
1. Simplify schema requirements
2. Improve prompt engineering
3. Add better descriptions to schema fields
4. Test with mock responses first

### Issue: Tool Not Available

**Symptoms:**
- Tool not appearing in MCP clients
- "Tool not found" errors

**Solutions:**
1. **Check schema file name**: Must be `{name}.json` where `name` matches the schema's `"name"` field
2. **Restart the server**: Schema files are loaded at startup
3. **Add tool to `autoApprove` list** in MCP configuration
4. **Restart MCP client** after configuration changes
5. **Verify schema syntax**: Use `python -c "import json; json.load(open('your_schema.json'))"`

## Advanced Features

### Conditional Fields

Use `oneOf`, `anyOf`, or `allOf` for complex validation:

```json
{
  "properties": {
    "contact": {
      "oneOf": [
        {
          "properties": {
            "type": {"const": "email"},
            "email": {"type": "string", "format": "email"}
          },
          "required": ["type", "email"]
        },
        {
          "properties": {
            "type": {"const": "phone"},
            "phone": {"type": "string"}
          },
          "required": ["type", "phone"]
        }
      ]
    }
  }
}
```

### Schema Addition via Tool

You can also add schemas using the `add_schema` tool (requires restart):

```
@fixed-schema add_schema schema_name: "weather_report" schema_definition: "{\"type\": \"object\", \"properties\": {\"location\": {\"type\": \"string\"}, \"temperature\": {\"type\": \"number\"}, \"conditions\": {\"type\": \"string\"}}, \"required\": [\"location\", \"temperature\", \"conditions\"]}" description: "Weather report information"
```

This immediately creates the `get_weather_report` tool without restarting!

## Next Steps

1. **Start simple** - Create a basic schema first
2. **Test thoroughly** - Validate both schema and responses
3. **Iterate** - Refine based on actual usage
4. **Document** - Add your schema to project documentation
5. **Share** - Consider contributing useful schemas back to the project

For more information, see:
- [JSON Schema Documentation](https://json-schema.org/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Main Project README](README.md)