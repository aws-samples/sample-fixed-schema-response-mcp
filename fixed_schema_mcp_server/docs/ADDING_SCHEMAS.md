# Adding New Schemas Guide

This guide explains how to add custom schemas to the Fixed Schema Response MCP Server to support new types of structured responses.

## Overview

The MCP server uses JSON schemas to define the structure of responses. Each schema consists of:
1. **Schema Definition** - JSON file defining the response structure
2. **Tool Function** - Python function that uses the schema
3. **Configuration** - Adding the tool to MCP client configurations

## Step-by-Step Process

### Step 1: Create a Schema File

Create a new JSON file in the `fixed_schema_mcp_server/test_config/schemas/` directory.

**Example: Creating a `book_review.json` schema**

```bash
cd fixed_schema_mcp_server/test_config/schemas
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
  }
}
```

### Step 2: Add Tool Function

Edit `fixed_schema_mcp_server/fastmcp_server.py` to add a new tool function.

Add this function before the `if __name__ == "__main__":` line:

```python
@mcp.tool()
def get_book_review(book_title: str, author: str = None) -> Dict[str, Any]:
    """
    Get a detailed book review.
    
    Args:
        book_title: Title of the book to review
        author: Author of the book (optional, helps with accuracy)
    
    Returns:
        Book review information in a structured format
    """
    logger.info(f"Generating book review for: {book_title} by {author or 'unknown author'}")
    
    if author:
        prompt = f"Please provide a detailed review of the book '{book_title}' by {author}. Include title, author, ISBN, rating (1-5), detailed review, genres, publication year, recommendation, and similar books."
    else:
        prompt = f"Please provide a detailed review of the book '{book_title}'. Include title, author, ISBN, rating (1-5), detailed review, genres, publication year, recommendation, and similar books."
    
    return invoke_claude(prompt, "book_review")
```

### Step 3: Add Mock Response Support

Add a mock response case in the `generate_mock_response` function in `fastmcp_server.py`:

```python
def generate_mock_response(prompt: str, schema_name: str) -> Dict[str, Any]:
    """
    Generate a mock response based on the schema.
    """
    logger.info(f"Generating mock response for schema: {schema_name}")
    
    # ... existing cases ...
    
    elif schema_name == "book_review":
        book_title = "Sample Book"
        if "'" in prompt:
            # Try to extract book title from prompt
            import re
            match = re.search(r"'([^']+)'", prompt)
            if match:
                book_title = match.group(1)
        
        return {
            "title": book_title,
            "author": "Sample Author",
            "isbn": "978-0-123456-78-9",
            "rating": 4.2,
            "review": f"This is a comprehensive review of {book_title}. The book offers valuable insights and is well-written with engaging content that keeps readers interested throughout.",
            "genres": ["Fiction", "Drama"],
            "publication_year": 2023,
            "recommended": True,
            "similar_books": [
                "Similar Book 1",
                "Similar Book 2",
                "Similar Book 3"
            ]
        }
    
    # ... rest of function ...
```

### Step 4: Update MCP Client Configurations

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

### Step 5: Test Your New Schema

1. **Test the server**:
   ```bash
   cd fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```

2. **Test with the test client**:
   ```bash
   # You'll need to update test_client.py to support the new tool
   # Or test directly in Kiro/Q Chat
   ```

3. **Test in Kiro**:
   ```
   @fixed-schema get_book_review book_title: "The Great Gatsby" author: "F. Scott Fitzgerald"
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

## Tool Function Patterns

### Basic Tool Function

```python
@mcp.tool()
def get_schema_name(primary_param: str, optional_param: str = None) -> Dict[str, Any]:
    """
    Brief description of what this tool does.
    
    Args:
        primary_param: Description of the main parameter
        optional_param: Description of optional parameter
    
    Returns:
        Structured data matching the schema
    """
    logger.info(f"Generating {schema_name} for: {primary_param}")
    
    # Build prompt based on parameters
    prompt = f"Generate {schema_name} for {primary_param}"
    if optional_param:
        prompt += f" with {optional_param}"
    
    return invoke_claude(prompt, "schema_name")
```

### Tool Function with Multiple Parameters

```python
@mcp.tool()
def get_complex_data(
    required_param: str,
    category: str = "general",
    include_details: bool = True,
    max_items: int = 10
) -> Dict[str, Any]:
    """
    Generate complex structured data.
    
    Args:
        required_param: The main subject
        category: Category to focus on
        include_details: Whether to include detailed information
        max_items: Maximum number of items to return
    
    Returns:
        Complex structured data
    """
    logger.info(f"Generating complex data for: {required_param}")
    
    prompt = f"Generate detailed information about {required_param}"
    if category != "general":
        prompt += f" in the {category} category"
    if include_details:
        prompt += " with comprehensive details"
    prompt += f" limited to {max_items} items"
    
    return invoke_claude(prompt, "complex_schema")
```

## Testing Your Schema

### 1. Schema Validation Test

Create a test to validate your schema works:

```python
# Add to test_schemas.py or create a new test file
import json
import jsonschema

def test_book_review_schema():
    # Load your schema
    with open('test_config/schemas/book_review.json', 'r') as f:
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
1. Add tool to `autoApprove` list in MCP configuration
2. Restart MCP client after changes
3. Check function name matches expected pattern
4. Verify `@mcp.tool()` decorator is present

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

### Dynamic Schema Loading

For advanced use cases, you can modify the `load_schemas()` function to support dynamic schema loading or schema inheritance.

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