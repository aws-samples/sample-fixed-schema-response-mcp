# Fixed Schema Response MCP Server

A Model Context Protocol (MCP) server that processes user queries and returns responses in a fixed schema format using FastMCP and AWS Bedrock Claude.

## Quick Start

1. **Setup** (run once):
   ```bash
   ./fixed_schema_mcp_server/setup.sh
   ```

2. **Run the server**:
   ```bash
   ./fixed_schema_mcp_server/run_fastmcp.sh
   ```

3. **Use in Kiro**:
   ```
   @fixed-schema get_product_info product_name: "iPhone 15 Pro"
   ```

## Documentation

For complete documentation, see: [`fixed_schema_mcp_server/README.md`](fixed_schema_mcp_server/README.md)

## Features

- **FastMCP Integration**: Built on the FastMCP framework
- **AWS Bedrock Integration**: Uses Claude 4 Sonnet for high-quality responses
- **Fallback Mechanism**: Provides mock responses when AWS credentials are not available
- **Kiro Integration**: Seamlessly works with Kiro as an MCP server
- **Schema-Based Responses**: Define JSON schemas to structure AI-generated content

## Available Tools

1. `get_product_info`: Get detailed information about a product
2. `get_person_profile`: Get profile information about a person
3. `get_api_endpoint`: Get documentation for an API endpoint
4. `get_troubleshooting_guide`: Get a troubleshooting guide for a technical issue
5. `get_article_summary`: Get a summary of an article or topic

## License

This project is licensed under the MIT License.