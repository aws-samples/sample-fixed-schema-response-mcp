# Schema Definition Guide

## Introduction

The Fixed Schema Response MCP Server uses JSON Schema to define the structure of responses. This guide explains how to create and use schemas to ensure consistent, structured responses from language models.

## Schema File Format

Schema files are JSON files that define the structure of responses. Each schema file should have the following structure:

```json
{
  "name": "schema_name",
  "description": "Description of the schema",
  "schema": {
    // JSON Schema definition
  },
  "system_prompt": "System prompt to guide the model's response generation"
}
```

### Fields

| Field | Description | Required |
|-------|-------------|----------|
| `name` | The name of the schema, used to reference it in requests | Yes |
| `description` | A description of the schema's purpose | No |
| `schema` | The JSON Schema definition | Yes |
| `system_prompt` | A system prompt to guide the model's response generation | No |

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

### Constraints

You can add constraints to values:

```json
{
  "type": "string",
  "minLength": 1,
  "maxLength": 100
}
```

```json
{
  "type": "number",
  "minimum": 0,
  "maximum": 100
}
```

## Examples of Common Schemas

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
      }
    }
  },
  "system_prompt": "You are a product information assistant. Provide information about products in a structured format."
}
```

### FAQ Schema

```json
{
  "name": "faq",
  "description": "Schema for FAQ responses",
  "schema": {
    "type": "object",
    "required": ["question", "answer"],
    "properties": {
      "question": {
        "type": "string",
        "description": "The original question"
      },
      "answer": {
        "type": "string",
        "description": "The answer to the question"
      },
      "related_questions": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Related questions that might be of interest"
      },
      "sources": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["title", "url"],
          "properties": {
            "title": {
              "type": "string",
              "description": "The title of the source"
            },
            "url": {
              "type": "string",
              "description": "The URL of the source"
            }
          }
        },
        "description": "Sources of information"
      }
    }
  },
  "system_prompt": "You are a helpful assistant answering questions. Provide detailed answers with related questions and sources when available."
}
```

### Code Explanation Schema

```json
{
  "name": "code_explanation",
  "description": "Schema for code explanation responses",
  "schema": {
    "type": "object",
    "required": ["explanation", "key_concepts"],
    "properties": {
      "explanation": {
        "type": "string",
        "description": "A detailed explanation of the code"
      },
      "key_concepts": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["concept", "description"],
          "properties": {
            "concept": {
              "type": "string",
              "description": "The name of the concept"
            },
            "description": {
              "type": "string",
              "description": "A description of the concept"
            }
          }
        },
        "description": "Key concepts used in the code"
      },
      "potential_issues": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Potential issues or improvements for the code"
      }
    }
  },
  "system_prompt": "You are a code explanation assistant. Explain code snippets in a clear and structured way, highlighting key concepts and potential issues."
}
```

## Schema Validation

The Fixed Schema Response MCP Server validates responses against the specified schema. If a response doesn't conform to the schema, the server will attempt to fix it or return an error.

### Validation Process

1. The server receives a request with a specified schema
2. The server generates a response using the model
3. The server validates the response against the schema
4. If the response is valid, it's returned to the client
5. If the response is invalid, the server attempts to fix it
6. If the response can't be fixed, an error is returned

### Common Validation Errors

| Error | Description | Solution |
|-------|-------------|----------|
| Missing required field | A required field is missing from the response | Ensure the system prompt clearly indicates all required fields |
| Invalid type | A field has the wrong type | Specify the expected type in the system prompt |
| Constraint violation | A field violates a constraint (e.g., minimum value) | Specify constraints in the system prompt |

### Improving Validation Success

To improve the chances of generating valid responses:

1. Use clear and specific system prompts
2. Include descriptions for each field in the schema
3. Start with simpler schemas and gradually add complexity
4. Test schemas with different queries to ensure they work as expected

## Advanced Schema Features

### Nested Objects

You can define nested objects in your schema:

```json
{
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string"
        },
        "address": {
          "type": "object",
          "properties": {
            "street": {
              "type": "string"
            },
            "city": {
              "type": "string"
            }
          }
        }
      }
    }
  }
}
```

### Enumerations

You can restrict a field to a set of predefined values:

```json
{
  "type": "string",
  "enum": ["red", "green", "blue"]
}
```

### Pattern Matching

You can use regular expressions to validate string formats:

```json
{
  "type": "string",
  "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
}
```

## Best Practices

1. **Keep schemas simple**: Start with simple schemas and add complexity as needed
2. **Use descriptive field names**: Choose field names that clearly indicate their purpose
3. **Add descriptions**: Include descriptions for each field to guide the model
4. **Test thoroughly**: Test schemas with various queries to ensure they work as expected
5. **Iterate and refine**: Refine schemas based on actual usage and feedback