# FastMCP API Documentation

## Introduction

The Fixed Schema Response MCP Server (FastMCP Edition) provides a set of tools for generating structured responses using AWS Bedrock Claude 4 Sonnet. This document describes the available tools, their parameters, and response formats.

## MCP Tools

The server provides the following MCP tools that can be used in Kiro:

### 1. get_product_info

Get detailed information about a product.

#### Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `product_name` | string | Name of the product to get information about | Yes |

#### Response Format

```json
{
  "name": "string",
  "description": "string",
  "price": number,
  "category": "string",
  "features": ["string"],
  "rating": number,
  "inStock": boolean
}
```

#### Example Usage

```
@fixed-schema get_product_info product_name: "iPhone 15 Pro"
```

### 2. get_person_profile

Get profile information about a person.

#### Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `person_name` | string | Name of the person to get profile for | Yes |

#### Response Format

```json
{
  "name": "string",
  "age": number,
  "occupation": "string",
  "skills": ["string"],
  "contact": {
    "email": "string",
    "phone": "string"
  }
}
```

#### Example Usage

```
@fixed-schema get_person_profile person_name: "Elon Musk"
```

### 3. get_api_endpoint

Get documentation for an API endpoint.

#### Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `endpoint_name` | string | Name of the API endpoint to get documentation for | Yes |

#### Response Format

```json
{
  "path": "string",
  "method": "string",
  "description": "string",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "required": boolean,
      "description": "string"
    }
  ],
  "responses": [
    {
      "code": number,
      "description": "string",
      "example": object
    }
  ]
}
```

#### Example Usage

```
@fixed-schema get_api_endpoint endpoint_name: "user authentication"
```

### 4. get_troubleshooting_guide

Get a troubleshooting guide for a technical issue.

#### Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `issue` | string | Description of the technical issue to troubleshoot | Yes |

#### Response Format

```json
{
  "issue": "string",
  "symptoms": ["string"],
  "causes": ["string"],
  "solutions": [
    {
      "step": number,
      "description": "string"
    }
  ],
  "preventionTips": ["string"]
}
```

#### Example Usage

```
@fixed-schema get_troubleshooting_guide issue: "computer won't start"
```

### 5. get_article_summary

Get a summary of an article or topic.

#### Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `topic` | string | Topic or article title to summarize | Yes |

#### Response Format

```json
{
  "title": "string",
  "author": "string",
  "date": "string",
  "summary": "string",
  "keyPoints": ["string"],
  "conclusion": "string"
}
```

#### Example Usage

```
@fixed-schema get_article_summary topic: "artificial intelligence"
```

## Implementation Details

### AWS Bedrock Integration

The server uses AWS Bedrock Claude 4 Sonnet to generate responses. When a tool is invoked, the server:

1. Constructs a prompt for Claude based on the tool parameters
2. Sends the prompt to Claude with the appropriate schema
3. Parses and validates the response against the schema
4. Returns the structured data to Kiro

If AWS Bedrock is not available (e.g., due to missing credentials), the server falls back to generating mock responses that match the schema structure.

### Mock Response Generation

When AWS Bedrock is not available, the server generates mock responses based on the tool parameters. These responses follow the schema structure but contain generic information.

### Error Handling

If an error occurs during response generation, the server will:

1. Log the error with details
2. Fall back to mock responses if possible
3. Return an error response if recovery fails

## Testing the API

You can test the API using the included test_client.py script:

```bash
python test_client.py --product "iPhone 15 Pro"
python test_client.py --person "Elon Musk"
python test_client.py --api "user authentication"
python test_client.py --troubleshoot "computer won't start"
python test_client.py --article "artificial intelligence"
```

## Adding Custom Tools

To add a custom tool:

1. Create a new schema file in the `test_config/schemas` directory
2. Add a new tool function to the `fastmcp_server.py` file:

```python
@mcp.tool()
def get_custom_data(custom_param: str) -> Dict[str, Any]:
    """
    Get custom data.
    
    Args:
        custom_param: Custom parameter
    
    Returns:
        Custom data in a structured format
    """
    logger.info(f"Generating custom data for: {custom_param}")
    
    prompt = f"Please provide custom data for {custom_param}."
    return invoke_claude(prompt, "custom_schema")
```

3. Update the Kiro MCP configuration to include the new tool in the autoApprove list