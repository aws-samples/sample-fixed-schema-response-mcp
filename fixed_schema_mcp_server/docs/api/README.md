# API Documentation

## Introduction

The Fixed Schema Response MCP Server provides a simple API for generating structured responses from language models. This document describes the API endpoints, request/response formats, and error handling.

## API Endpoints

### Generate Response

Generates a structured response based on a user query and a specified schema.

- **Endpoint**: `/generate`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Format

```json
{
  "query": "string",
  "schema": "string",
  "parameters": {
    "temperature": number,
    "top_p": number,
    "max_tokens": number
  }
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `query` | string | The user query to process | Yes |
| `schema` | string | The name of the schema to use | Yes |
| `parameters` | object | Model parameters to override defaults | No |

#### Response Format

```json
{
  "status": "success",
  "data": {
    // Schema-specific response data
  },
  "metadata": {
    "model": "string",
    "processing_time": number
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | The status of the request (`success` or `error`) |
| `data` | object | The structured response data (format depends on the schema) |
| `metadata` | object | Metadata about the response |

#### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "string",
    "message": "string",
    "details": {
      // Error-specific details
    }
  },
  "metadata": {
    "model": "string",
    "processing_time": number
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `error` for error responses |
| `error` | object | Error information |
| `error.code` | string | Error code |
| `error.message` | string | Human-readable error message |
| `error.details` | object | Additional error details |
| `metadata` | object | Metadata about the response |

### List Schemas

Lists all available schemas.

- **Endpoint**: `/schemas`
- **Method**: `GET`

#### Response Format

```json
{
  "status": "success",
  "data": {
    "schemas": [
      {
        "name": "string",
        "description": "string"
      }
    ]
  }
}
```

### Get Schema

Gets details about a specific schema.

- **Endpoint**: `/schemas/{schema_name}`
- **Method**: `GET`

#### Response Format

```json
{
  "status": "success",
  "data": {
    "name": "string",
    "description": "string",
    "schema": {
      // JSON Schema definition
    }
  }
}
```

### Server Status

Gets the current status of the server.

- **Endpoint**: `/status`
- **Method**: `GET`

#### Response Format

```json
{
  "status": "success",
  "data": {
    "server_status": "string",
    "uptime": number,
    "model_status": "string",
    "request_count": number
  }
}
```

## Request/Response Examples

### Example 1: Product Information

#### Request

```json
{
  "query": "Tell me about the latest iPhone",
  "schema": "product_info",
  "parameters": {
    "temperature": 0.5
  }
}
```

#### Response

```json
{
  "status": "success",
  "data": {
    "name": "iPhone 15 Pro",
    "description": "The latest flagship smartphone from Apple featuring a powerful A17 Pro chip, advanced camera system, and titanium design.",
    "price": 999.99,
    "category": "Smartphones",
    "features": [
      "A17 Pro chip",
      "48MP camera system",
      "Titanium design",
      "Action button",
      "USB-C connector"
    ]
  },
  "metadata": {
    "model": "gpt-4",
    "processing_time": 1.25
  }
}
```

### Example 2: FAQ Response

#### Request

```json
{
  "query": "How do I reset my password?",
  "schema": "faq"
}
```

#### Response

```json
{
  "status": "success",
  "data": {
    "question": "How do I reset my password?",
    "answer": "To reset your password, click on the 'Forgot Password' link on the login page. Enter your email address, and we'll send you a password reset link. Click the link in the email and follow the instructions to create a new password.",
    "related_questions": [
      "How do I change my password?",
      "What should I do if I don't receive the password reset email?",
      "How can I create a strong password?"
    ],
    "sources": [
      {
        "title": "Password Reset Guide",
        "url": "https://example.com/help/password-reset"
      }
    ]
  },
  "metadata": {
    "model": "gpt-4",
    "processing_time": 0.87
  }
}
```

### Example 3: Error Response

#### Request

```json
{
  "query": "Tell me about the latest iPhone",
  "schema": "nonexistent_schema"
}
```

#### Response

```json
{
  "status": "error",
  "error": {
    "code": "schema_not_found",
    "message": "The specified schema 'nonexistent_schema' was not found",
    "details": {
      "available_schemas": ["product_info", "faq", "code_explanation"]
    }
  },
  "metadata": {
    "processing_time": 0.05
  }
}
```

## Error Handling

The Fixed Schema Response MCP Server uses a consistent error handling approach. All errors are returned with a status code of `error` and include detailed information about the error.

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `invalid_request` | The request format is invalid | 400 |
| `schema_not_found` | The specified schema was not found | 404 |
| `schema_validation_failed` | The generated response failed schema validation | 422 |
| `model_error` | An error occurred while generating the response | 500 |
| `rate_limit_exceeded` | The rate limit for API requests has been exceeded | 429 |
| `server_error` | An internal server error occurred | 500 |

### Error Details

The `details` field in error responses provides additional information about the error. The content of this field depends on the error type:

#### Schema Validation Errors

```json
{
  "status": "error",
  "error": {
    "code": "schema_validation_failed",
    "message": "Generated response failed schema validation",
    "details": {
      "missing_fields": ["price"],
      "invalid_fields": {
        "category": "Expected string, got number"
      }
    }
  }
}
```

#### Rate Limit Errors

```json
{
  "status": "error",
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 10,
      "reset_at": "2023-07-23T15:30:00Z"
    }
  }
}
```

### Error Recovery

The server implements several error recovery mechanisms:

1. **Schema Validation Failures**: If a response fails schema validation, the server will attempt to fix it by:
   - Adding missing required fields
   - Converting fields to the correct type
   - Removing extra fields

2. **Model Errors**: If a model error occurs, the server will:
   - Retry the request up to 3 times
   - Fall back to a different model if configured
   - Return a detailed error if recovery fails

3. **Rate Limiting**: If rate limits are exceeded, the server will:
   - Queue requests for later processing
   - Implement exponential backoff for retries
   - Return a rate limit error with reset time

## API Client Libraries

The Fixed Schema Response MCP Server provides client libraries for common programming languages:

### Python

```python
from fixed_schema_mcp_client import FixedSchemaMCPClient

client = FixedSchemaMCPClient(host="localhost", port=8000)
response = client.generate(
    query="Tell me about the latest iPhone",
    schema="product_info",
    parameters={"temperature": 0.5}
)

print(response.data)
```

### JavaScript

```javascript
const { FixedSchemaMCPClient } = require('fixed-schema-mcp-client');

const client = new FixedSchemaMCPClient({ host: 'localhost', port: 8000 });
client.generate({
  query: 'Tell me about the latest iPhone',
  schema: 'product_info',
  parameters: { temperature: 0.5 }
})
.then(response => {
  console.log(response.data);
})
.catch(error => {
  console.error(error);
});
```

## API Versioning

The API uses versioning to ensure backward compatibility. The current version is v1.

- All endpoints are prefixed with `/v1`
- Future versions will use `/v2`, `/v3`, etc.
- The server supports multiple API versions simultaneously

## Rate Limiting

The server implements rate limiting to prevent abuse:

- 10 requests per minute per IP address
- 1000 requests per day per API key
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: The rate limit ceiling
  - `X-RateLimit-Remaining`: The number of requests left
  - `X-RateLimit-Reset`: The time when the rate limit resets