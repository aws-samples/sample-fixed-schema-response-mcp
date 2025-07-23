# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Issue: Package Installation Fails

**Symptoms:**
- Error messages during pip installation
- Missing dependencies

**Solutions:**
1. Ensure you have the latest version of pip:
   ```bash
   pip install --upgrade pip
   ```

2. Check Python version compatibility:
   ```bash
   python --version
   ```
   The Fixed Schema Response MCP Server requires Python 3.8 or higher.

3. Install with verbose output to identify specific issues:
   ```bash
   pip install fixed-schema-mcp-server -v
   ```

#### Issue: Missing Dependencies

**Symptoms:**
- ImportError when running the server
- ModuleNotFoundError exceptions

**Solutions:**
1. Reinstall with all dependencies:
   ```bash
   pip install fixed-schema-mcp-server[all]
   ```

2. Install specific missing dependencies:
   ```bash
   pip install jsonschema pydantic fastapi uvicorn
   ```

### Configuration Issues

#### Issue: Configuration File Not Found

**Symptoms:**
- Error message: "Configuration file not found"
- Server fails to start

**Solutions:**
1. Verify the path to the configuration file:
   ```bash
   fixed-schema-mcp-server --config /absolute/path/to/config.json
   ```

2. Create a default configuration file:
   ```bash
   fixed-schema-mcp-server --create-config
   ```

#### Issue: Invalid Configuration Format

**Symptoms:**
- Error message: "Invalid configuration format"
- JSON parsing errors

**Solutions:**
1. Validate your JSON configuration:
   ```bash
   python -c "import json; json.load(open('config.json'))"
   ```

2. Check for common JSON syntax errors:
   - Missing commas between items
   - Trailing commas (not allowed in JSON)
   - Unquoted keys
   - Single quotes instead of double quotes

### Schema Issues

#### Issue: Schema File Not Found

**Symptoms:**
- Error message: "Schema file not found"
- Schema validation failures

**Solutions:**
1. Verify the schema directory path in your configuration:
   ```json
   {
     "schemas": {
       "path": "./schemas"
     }
   }
   ```

2. Ensure schema files exist in the specified directory:
   ```bash
   ls -la ./schemas
   ```

#### Issue: Invalid Schema Format

**Symptoms:**
- Error message: "Invalid schema format"
- Schema validation failures

**Solutions:**
1. Validate your schema JSON:
   ```bash
   python -c "import json; json.load(open('schemas/my_schema.json'))"
   ```

2. Verify schema structure against the required format:
   ```json
   {
     "name": "schema_name",
     "description": "Schema description",
     "schema": {
       "type": "object",
       "properties": {}
     }
   }
   ```

### Model API Issues

#### Issue: API Key Not Found

**Symptoms:**
- Error message: "API key not found" or "Invalid API key"
- Authentication failures with the model provider

**Solutions:**
1. Set the API key in your configuration:
   ```json
   {
     "model": {
       "provider": "openai",
       "api_key": "YOUR_API_KEY"
     }
   }
   ```

2. Set the API key as an environment variable:
   ```bash
   export FIXED_SCHEMA_MCP_MODEL_API_KEY=your_api_key
   ```

#### Issue: Rate Limit Exceeded

**Symptoms:**
- Error message: "Rate limit exceeded"
- Requests failing after a certain number

**Solutions:**
1. Implement request throttling in your application
2. Increase the rate limit with your model provider (if possible)
3. Configure the server to use connection pooling:
   ```json
   {
     "model": {
       "connection_pool": {
         "max_connections": 5,
         "timeout": 60
       }
     }
   }
   ```

### Response Validation Issues

#### Issue: Schema Validation Failures

**Symptoms:**
- Error message: "Schema validation failed"
- Missing or invalid fields in responses

**Solutions:**
1. Check the schema requirements:
   ```bash
   fixed-schema-mcp-server --validate-schema schemas/my_schema.json
   ```

2. Improve the system prompt to guide the model:
   ```json
   {
     "system_prompt": "You MUST follow this exact format in your response..."
   }
   ```

3. Simplify the schema requirements if they're too complex

#### Issue: Inconsistent Response Format

**Symptoms:**
- Sometimes responses are valid, sometimes not
- Unpredictable response structure

**Solutions:**
1. Lower the temperature parameter for more consistent outputs:
   ```json
   {
     "parameters": {
       "temperature": 0.2
     }
   }
   ```

2. Use a more deterministic model if available
3. Add more examples in the system prompt

### Server Issues

#### Issue: Server Won't Start

**Symptoms:**
- Error messages during startup
- Process exits immediately

**Solutions:**
1. Check for port conflicts:
   ```bash
   lsof -i :8000
   ```

2. Run with debug logging:
   ```bash
   fixed-schema-mcp-server --log-level debug
   ```

3. Check system resources (memory, disk space)

#### Issue: Server Crashes Under Load

**Symptoms:**
- Server crashes when handling multiple requests
- Memory usage increases over time

**Solutions:**
1. Configure request queuing:
   ```json
   {
     "server": {
       "max_concurrent_requests": 5,
       "queue_size": 100
     }
   }
   ```

2. Implement connection pooling:
   ```json
   {
     "model": {
       "connection_pool": {
         "max_connections": 10
       }
     }
   }
   ```

3. Increase server resources if possible

## Debugging Tips

### Enable Debug Logging

Set the log level to debug for more detailed information:

```bash
fixed-schema-mcp-server --log-level debug
```

Or in the configuration:

```json
{
  "server": {
    "log_level": "debug"
  }
}
```

### Validate Configuration and Schemas

Use the built-in validation tools:

```bash
# Validate configuration
fixed-schema-mcp-server --validate-config config.json

# Validate schema
fixed-schema-mcp-server --validate-schema schemas/my_schema.json
```

### Test Individual Components

Test the schema validation independently:

```bash
fixed-schema-mcp-server --test-schema schemas/my_schema.json --test-data test_data.json
```

Test the model connection:

```bash
fixed-schema-mcp-server --test-model
```

### Monitor Server Metrics

Enable metrics collection:

```json
{
  "server": {
    "metrics": {
      "enabled": true,
      "port": 9090
    }
  }
}
```

Access metrics at `http://localhost:9090/metrics`

### Use the Debug Endpoint

The server provides a debug endpoint for troubleshooting:

```bash
curl http://localhost:8000/debug/status
```

## Frequently Asked Questions (FAQ)

### General Questions

#### Q: What is the Fixed Schema Response MCP Server?

A: The Fixed Schema Response MCP Server is a Model Context Protocol (MCP) server that processes user queries and returns responses in a predefined structured format (e.g., JSON). It ensures that all responses follow a consistent structure, making them predictable and easily consumable by applications.

#### Q: How does it differ from regular language model APIs?

A: Unlike regular language model APIs that return free-form text, the Fixed Schema Response MCP Server constrains responses to follow a predefined structure. This makes the outputs more predictable and easier to parse programmatically.

### Installation and Setup

#### Q: What are the system requirements?

A: The server requires Python 3.8 or higher and works on Linux, macOS, and Windows.

#### Q: Can I run the server in a Docker container?

A: Yes, a Docker image is available:

```bash
docker pull fixed-schema-mcp-server
docker run -p 8000:8000 -v ./config.json:/app/config.json fixed-schema-mcp-server
```

#### Q: How do I update to the latest version?

A: Use pip to update:

```bash
pip install --upgrade fixed-schema-mcp-server
```

### Configuration

#### Q: Can I use multiple model providers?

A: Yes, you can configure multiple model providers and specify which one to use for each request:

```json
{
  "model": {
    "providers": {
      "openai": {
        "api_key": "YOUR_OPENAI_API_KEY",
        "model_name": "gpt-4"
      },
      "anthropic": {
        "api_key": "YOUR_ANTHROPIC_API_KEY",
        "model_name": "claude-2"
      }
    },
    "default_provider": "openai"
  }
}
```

#### Q: How do I configure rate limiting?

A: Add rate limiting configuration:

```json
{
  "server": {
    "rate_limit": {
      "requests_per_minute": 60,
      "requests_per_day": 1000
    }
  }
}
```

### Schemas

#### Q: How many schemas can I define?

A: There's no hard limit on the number of schemas you can define. However, for performance reasons, it's recommended to keep the number of schemas reasonable (under 100).

#### Q: Can schemas reference each other?

A: Yes, you can use JSON Schema's `$ref` keyword to reference other schemas:

```json
{
  "type": "object",
  "properties": {
    "user": {
      "$ref": "user.json"
    }
  }
}
```

#### Q: How complex can schemas be?

A: Schemas can be as complex as needed, but very complex schemas may result in lower validation success rates. It's recommended to start with simpler schemas and gradually add complexity as needed.

### Performance

#### Q: How many requests per second can the server handle?

A: The performance depends on various factors including hardware, model provider, and schema complexity. With default settings on moderate hardware, the server can typically handle 5-10 requests per second.

#### Q: How can I improve performance?

A: See the [Performance Tuning Guide](../performance/README.md) for detailed recommendations.

### Troubleshooting

#### Q: Where can I find the server logs?

A: By default, logs are written to stdout/stderr. You can redirect them to a file:

```bash
fixed-schema-mcp-server > server.log 2>&1
```

Or configure logging in the configuration file:

```json
{
  "server": {
    "log_file": "/path/to/server.log"
  }
}
```

#### Q: How do I report bugs or request features?

A: Please submit issues on our GitHub repository: [https://github.com/yourusername/fixed-schema-mcp-server/issues](https://github.com/yourusername/fixed-schema-mcp-server/issues)