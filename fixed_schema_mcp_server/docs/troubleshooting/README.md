# Troubleshooting Guide for FastMCP Edition

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

3. Install dependencies manually:
   ```bash
   pip install fastmcp boto3 jsonschema
   ```

#### Issue: Missing Dependencies

**Symptoms:**
- ImportError when running the server
- ModuleNotFoundError exceptions

**Solutions:**
1. Install required dependencies:
   ```bash
   pip install fastmcp boto3 jsonschema
   ```

2. Check if FastMCP is installed correctly:
   ```bash
   python -c "import mcp.server.fastmcp; print('FastMCP installed')"
   ```

### AWS Credentials Issues

#### Issue: AWS Credentials Not Found

**Symptoms:**
- Warning message: "AWS credentials not found in environment variables"
- Server falls back to mock responses

**Solutions:**
1. Configure AWS credentials:
   ```bash
   aws configure
   ```

2. Check if AWS credentials are configured correctly:
   ```bash
   aws sts get-caller-identity
   ```

3. Set AWS credentials as environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

#### Issue: AWS Bedrock Access Denied

**Symptoms:**
- Error message: "AccessDeniedException" when invoking Bedrock
- Server falls back to mock responses

**Solutions:**
1. Verify that your AWS account has access to Amazon Bedrock:
   - Check the AWS console to ensure Bedrock is enabled for your account
   - Verify that you have the necessary IAM permissions

2. Check if the Claude model is available in your region:
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

3. If you don't have AWS Bedrock access, the server will automatically fall back to mock responses.

### Schema Issues

#### Issue: Schema File Not Found

**Symptoms:**
- Warning message: "Schemas directory not found"
- Server uses default schemas

**Solutions:**
1. Verify the schemas directory exists:
   ```bash
   ls -la fixed_schema_mcp_server/test_config/schemas
   ```

2. Ensure schema files have the correct format:
   ```bash
   python -c "import json; json.load(open('fixed_schema_mcp_server/test_config/schemas/product_info.json'))"
   ```

#### Issue: Invalid Schema Format

**Symptoms:**
- Error message: "Failed to load schema"
- Schema validation failures

**Solutions:**
1. Validate your schema JSON:
   ```bash
   python -c "import json; json.load(open('fixed_schema_mcp_server/test_config/schemas/my_schema.json'))"
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

### Setup Issues

#### Issue: Virtual Environment Not Found

**Symptoms:**
- Error message: "Virtual environment not found"
- Server fails to start

**Solutions:**
1. Run the setup script:
   ```bash
   ./setup.sh
   ```

2. Or manually create the virtual environment:
   ```bash
   python3 -m venv fixed_schema_mcp_venv
   source fixed_schema_mcp_venv/bin/activate
   pip install fastmcp boto3 jsonschema
   ```

#### Issue: Dependencies Not Installed

**Symptoms:**
- Error message: "FastMCP not installed"
- Import errors when starting the server

**Solutions:**
1. Run the setup script:
   ```bash
   ./setup.sh
   ```

2. Or manually install dependencies:
   ```bash
   source fixed_schema_mcp_venv/bin/activate
   pip install fastmcp boto3 jsonschema
   ```

### Kiro Integration Issues

#### Issue: Kiro Can't Connect to the Server

**Symptoms:**
- Error message in Kiro: "Failed to connect to MCP server"
- No response from the server

**Solutions:**
1. Make sure you've run the setup first:
   ```bash
   ./setup.sh
   ```

2. Check that the run_fastmcp.sh script has execute permissions:
   ```bash
   chmod +x fixed_schema_mcp_server/run_fastmcp.sh
   ```

3. Verify that the path in the Kiro MCP configuration is correct:
   ```json
   {
     "mcpServers": {
       "fixed-schema": {
         "command": "/absolute/path/to/fixed_schema_mcp_server/run_fastmcp.sh"
       }
     }
   }
   ```

4. Try running the server manually to check for errors:
   ```bash
   ./fixed_schema_mcp_server/run_fastmcp.sh
   ```

#### Issue: Tool Not Found in Kiro

**Symptoms:**
- Error message in Kiro: "Tool not found"
- No response from the server

**Solutions:**
1. Verify that the tool name is correct:
   ```
   @fixed-schema get_product_info product_name: "iPhone"
   ```

2. Check that the tool is registered in the fastmcp_server.py file:
   ```python
   @mcp.tool()
   def get_product_info(product_name: str) -> Dict[str, Any]:
       # ...
   ```

3. Make sure the tool is included in the autoApprove list in the Kiro MCP configuration:
   ```json
   {
     "mcpServers": {
       "fixed-schema": {
         "autoApprove": [
           "get_product_info",
           "get_article_summary",
           "get_person_profile",
           "get_api_endpoint",
           "get_troubleshooting_guide"
         ]
       }
     }
   }
   ```

### Response Issues

#### Issue: Mock Responses Instead of Real Responses

**Symptoms:**
- Generic responses that don't match the query
- Warning message: "AWS Bedrock client not available, using mock response"

**Solutions:**
1. Configure AWS credentials as described above
2. Verify that your AWS account has access to Amazon Bedrock
3. Check if the Claude model is available in your region

#### Issue: Response Format Issues

**Symptoms:**
- Error message: "Failed to parse Claude response as JSON"
- Incomplete or malformed responses

**Solutions:**
1. Check the schema definition to ensure it's not too complex
2. Simplify the schema if necessary
3. The server will automatically fall back to mock responses if parsing fails

## Debugging Tips

### Enable Debug Logging

Set the log level to debug for more detailed information:

```bash
FASTMCP_LOG_LEVEL=DEBUG ./fixed_schema_mcp_server/run_fastmcp.sh
```

Or in the Kiro MCP configuration:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "env": {
        "FASTMCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Test the Server Manually

Use the test_client.py script to test the server:

```bash
python fixed_schema_mcp_server/test_client.py --product "iPhone 15 Pro"
python fixed_schema_mcp_server/test_client.py --person "Elon Musk"
python fixed_schema_mcp_server/test_client.py --api "user authentication"
python fixed_schema_mcp_server/test_client.py --troubleshoot "computer won't start"
python fixed_schema_mcp_server/test_client.py --article "artificial intelligence"
```

### Test Schema Loading

Use the test_schemas.py script to test schema loading:

```bash
python fixed_schema_mcp_server/test_schemas.py fixed_schema_mcp_server/test_config/schemas
```

## Frequently Asked Questions (FAQ)

### General Questions

#### Q: What is the Fixed Schema Response MCP Server (FastMCP Edition)?

A: The Fixed Schema Response MCP Server (FastMCP Edition) is a Model Context Protocol (MCP) server built on the FastMCP framework that processes user queries and returns responses in a predefined structured format (e.g., JSON). It uses AWS Bedrock Claude 4 Sonnet to generate high-quality responses.

#### Q: How does it differ from regular language model APIs?

A: Unlike regular language model APIs that return free-form text, the Fixed Schema Response MCP Server constrains responses to follow a predefined structure. This makes the outputs more predictable and easier to parse programmatically.

### Installation and Setup

#### Q: What are the system requirements?

A: The server requires Python 3.8 or higher and works on Linux, macOS, and Windows.

#### Q: Do I need AWS credentials?

A: AWS credentials are optional. If you have AWS credentials and access to Amazon Bedrock, the server will use Claude 4 Sonnet to generate responses. If not, it will fall back to mock responses.

#### Q: How do I update to the latest version?

A: Since this is a custom implementation, you can update by pulling the latest code from the repository:

```bash
git pull
```

### Configuration

#### Q: Can I customize the schemas?

A: Yes, you can modify the existing schemas or add new ones by creating JSON files in the `test_config/schemas` directory and updating the `fastmcp_server.py` file to add new tool functions.

#### Q: Can I use a different model?

A: The server is currently configured to use AWS Bedrock Claude 4 Sonnet. If you want to use a different model, you'll need to modify the `fastmcp_server.py` file.

### Performance

#### Q: How many requests per second can the server handle?

A: The performance depends on various factors including hardware, AWS Bedrock availability, and schema complexity. With default settings on moderate hardware, the server can typically handle 5-10 requests per second.

#### Q: Is there any rate limiting?

A: The server doesn't implement rate limiting itself, but AWS Bedrock has its own rate limits. If you exceed these limits, the server will fall back to mock responses.