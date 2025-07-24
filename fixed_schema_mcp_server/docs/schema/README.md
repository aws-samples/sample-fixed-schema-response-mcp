# Schema Definition Guide for FastMCP Edition

## Introduction

The Fixed Schema Response MCP Server (FastMCP Edition) uses JSON Schema to define the structure of responses. This guide explains how to create and use schemas to ensure consistent, structured responses from AWS Bedrock Claude.

## Schema File Format

Schema files are JSON files that define the structure of responses. Each schema file should have the following structure:

```json
{
  "name": "schema_name",
  "description": "Description of the schema",
  "schema": {
    // JSON Schema definition
  }
}
```

### Fields

| Field | Description | Required |
|-------|-------------|----------|
| `name` | The name of the schema, used to reference it in requests | Yes |
| `description` | A description of the schema's purpose | Yes |
| `schema` | The JSON Schema definition | Yes |

## Schema Location

Schemas are stored in the `test_config/schemas` directory. The server automatically loads all schema files from this directory when it starts.

## Available Schemas

The Fixed Schema MCP Server includes the following schemas:

1. **Product Info** (`product_info.json`)
   - For generating structured information about products
   - Includes name, description, price, category, features, rating, and availability

2. **Person Profile** (`person_profile.json`)
   - For generating structured biographical information about people
   - Includes name, age, occupation, skills, and contact information

3. **API Endpoint Documentation** (`api_endpoint.json`)
   - For generating structured API endpoint documentation
   - Includes path, method, description, parameters, and responses

4. **Troubleshooting Guide** (`troubleshooting_guide.json`)
   - For generating structured technical troubleshooting guides
   - Includes issue, symptoms, causes, step-by-step solutions, and prevention tips

5. **Article Summary** (`article_summary.json`)
   - For generating structured summaries of articles or topics
   - Includes title, author, date, summary, key points, and conclusion

## JSON Schema Basics

The `schema` field uses [JSON Schema](https://json-schema.org/) to define the structure of responses. Here are some basic concepts:

### Types

JSON Schema supports the following types:

- `object`: A JSON object (key-value pairs)
- `array`: A JSON array
- `string`: A string value
- `number`: A numeric value
- `integer`: An integer value
- `boolean`: A boolean value (true/false)
- `null`: A null value

### Properties

For `object` types, you can define properties:

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "age": {
      "type": "integer"
    }
  }
}
```

### Required Properties

You can specify which properties are required:

```json
{
  "type": "object",
  "required": ["name", "age"],
  "properties": {
    "name": {
      "type": "string"
    },
    "age": {
      "type": "integer"
    }
  }
}
```

### Arrays

For `array` types, you can define the type of items:

```json
{
  "type": "array",
  "items": {
    "type": "string"
  }
}
```

## Examples of Schema Files

### Product Information Schema

```json
{
  "name": "product_info",
  "description": "Schema for product information responses",
  "schema": {
    "type": "object",
    "required": ["name", "description", "price", "category"],
    "properties": {
      "name": {
        "type": "string",
        "description": "The name of the product"
      },
      "description": {
        "type": "string",
        "description": "A detailed description of the product"
      },
      "price": {
        "type": "number",
        "description": "The price of the product in USD"
      },
      "category": {
        "type": "string",
        "description": "The category the product belongs to"
      },
      "features": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "List of product features"
      },
      "rating": {
        "type": "number",
        "description": "The product rating (0-5)"
      },
      "inStock": {
        "type": "boolean",
        "description": "Whether the product is in stock"
      }
    }
  }
}
```

### Person Profile Schema

```json
{
  "name": "person_profile",
  "description": "Schema for person profile information",
  "schema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "The person's name"
      },
      "age": {
        "type": "integer",
        "description": "The person's age"
      },
      "occupation": {
        "type": "string",
        "description": "The person's occupation"
      },
      "skills": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "The person's skills"
      },
      "contact": {
        "type": "object",
        "properties": {
          "email": {
            "type": "string",
            "description": "The person's email address"
          },
          "phone": {
            "type": "string",
            "description": "The person's phone number"
          }
        },
        "description": "The person's contact information"
      }
    },
    "required": ["name"]
  }
}
```

## Creating Custom Schemas

To create a custom schema:

1. Create a new JSON file in the `test_config/schemas` directory
2. Define the schema structure following the format above
3. Update the `fastmcp_server.py` file to add a new tool function for your schema

Example of adding a new tool function:

```python
@mcp.tool()
def get_custom_schema(custom_param: str) -> Dict[str, Any]:
    """
    Get custom schema information.
    
    Args:
        custom_param: Parameter for the custom schema
    
    Returns:
        Custom schema information in a structured format
    """
    logger.info(f"Generating custom schema for: {custom_param}")
    
    prompt = f"Please provide information about {custom_param} in the custom schema format."
    return invoke_claude(prompt, "custom_schema")
```

## Best Practices

1. **Keep schemas simple**: Start with simple schemas and add complexity as needed
2. **Use descriptive field names**: Choose field names that clearly indicate their purpose
3. **Add descriptions**: Include descriptions for each field to guide the model
4. **Test thoroughly**: Test schemas with the test_client.py script
5. **Iterate and refine**: Refine schemas based on actual usage and feedback