# Fixed Schema Response MCP Server (FastMCP Edition)

A Model Context Protocol (MCP) server that processes user queries and returns responses in a fixed schema format (e.g., JSON) using FastMCP. This server constrains model responses to follow a predefined structure, making outputs more predictable and easier to parse programmatically.

## Features

- **FastMCP Integration**: Built on the FastMCP framework for simplified MCP server development
- **Schema-Based Responses**: Define JSON schemas to structure AI-generated content
- **AWS Bedrock Integration**: Uses Claude 4 Sonnet for high-quality responses
- **Fallback Mechanism**: Provides mock responses when AWS credentials are not available
- **Kiro Integration**: Seamlessly works with Kiro as an MCP server
- **Dynamic Schema Loading**: Automatically loads schemas from the test_config directory

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- AWS credentials configured (for AWS Bedrock integration)
- FastMCP library

### Setup

#### Prerequisites
- Python 3.10 or higher
- `uv` package manager ([install uv](https://docs.astral.sh/uv/getting-started/installation/))

#### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/fixed-schema-mcp-server.git
cd fixed-schema-mcp-server/fixed_schema_mcp_server

# Test the server (uv will automatically install dependencies)
uv run fastmcp_server.py
```

That's it! `uv` automatically handles:
- Virtual environment creation
- Dependency installation (fastmcp, boto3, jsonschema)
- Python version management

#### Docker Setup (Alternative)

If you prefer using Docker:

```bash
# Clone the repository
git clone https://github.com/yourusername/fixed-schema-mcp-server.git
cd fixed-schema-mcp-server/fixed_schema_mcp_server

# Build the Docker image
docker build -t fixed-schema-mcp-server .

# Run the container
docker run -it --rm \
  -e AWS_ACCESS_KEY_ID=your_access_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret_key \
  -e AWS_DEFAULT_REGION=us-east-1 \
  fixed-schema-mcp-server
```

**Note**: The Docker container runs the server with stdio transport, suitable for process-based MCP communication.

## Quick Start

### 1. Configure AWS Credentials (Optional)

If you want to use AWS Bedrock for generating responses, configure your AWS credentials:

```bash
# Configure AWS CLI
aws configure
```

You'll need to enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (choose a region where Bedrock is available, like us-east-1 or us-west-2)
- Default output format (json)

If AWS credentials are not configured, the server will fall back to mock responses.

### 2. Schema Configuration

The server automatically loads schemas from the `test_config/schemas` directory. The following schemas are included:

- `product_info.json`: Schema for product information
- `person_profile.json`: Schema for person profiles
- `api_endpoint.json`: Schema for API endpoint documentation
- `troubleshooting_guide.json`: Schema for troubleshooting guides
- `article_summary.json`: Schema for article summaries

You can modify these schemas or add new ones by creating JSON files in the `test_config/schemas` directory.

### 3. Start the Server

Run the FastMCP server using uv:

```bash
cd fixed_schema_mcp_server
uv run fastmcp_server.py
```

### 4. Configure Kiro

The server is already configured for Kiro in `.kiro/settings/mcp.json`. The configuration uses `uv`:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/fixed_schema_mcp_server", "run", "fastmcp_server.py"],
      "env": {
        "FASTMCP_LOG_LEVEL": "DEBUG"
      },
      "disabled": false,
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

**Important**: Replace `/absolute/path/to/fixed_schema_mcp_server` with your actual path.

## Using the MCP Tools

The server provides the following MCP tools that can be used in Kiro:

1. `get_product_info`: Get detailed information about a product
2. `get_person_profile`: Get profile information about a person
3. `get_api_endpoint`: Get documentation for an API endpoint
4. `get_troubleshooting_guide`: Get a troubleshooting guide for a technical issue
5. `get_article_summary`: Get a summary of an article or topic

### Example Usage in Kiro

```
@fixed-schema get_product_info product_name: "iPhone 15 Pro"
@fixed-schema get_person_profile person_name: "Elon Musk"
@fixed-schema get_api_endpoint endpoint_name: "user authentication"
@fixed-schema get_troubleshooting_guide issue: "computer won't start"
@fixed-schema get_article_summary topic: "artificial intelligence"
```

## Troubleshooting

### AWS Credentials

If you're not seeing responses from AWS Bedrock:

1. Check that your AWS credentials are properly configured:
   ```bash
   aws sts get-caller-identity
   ```

2. Verify that your AWS account has access to Amazon Bedrock and the Claude model.

3. If you don't have AWS credentials, the server will automatically fall back to mock responses.

### Dependencies

If you encounter issues with missing dependencies:

```bash
# Check uv installation
uv --version

# Test dependency resolution
cd fixed_schema_mcp_server
uv run --help
```

### Kiro Integration

If Kiro is not connecting to the MCP server:

1. **Check that the path in the Kiro MCP configuration is correct**
2. **Ensure uv is installed and accessible:**
   ```bash
   which uv
   uv --version
   ```
3. **Try running the server manually to check for errors:**
   ```bash
   cd fixed_schema_mcp_server
   uv run fastmcp_server.py
   ```
4. **Check the absolute path in your Kiro config:**
   ```bash
   pwd  # Run this in the fixed_schema_mcp_server directory
   ```

## How It Works

The FastMCP server works by:

1. Loading schemas from the `test_config/schemas` directory
2. Registering MCP tools for each schema type
3. When a tool is invoked, it:
   - Constructs a prompt for AWS Bedrock Claude 4 Sonnet
   - Sends the prompt to Claude with the appropriate schema
   - Parses and validates the response against the schema
   - Returns the structured data to Kiro

If AWS Bedrock is not available, it falls back to generating mock responses that match the schema structure.

## Use Cases

- **Product Information**: Get structured information about products
- **Person Profiles**: Generate structured profiles for individuals
- **API Documentation**: Create structured API endpoint documentation
- **Troubleshooting**: Generate step-by-step troubleshooting guides
- **Article Summaries**: Create structured summaries of articles or topics

## Testing

You can test the server using the included test client:

```bash
cd fixed_schema_mcp_server

# Test different tools
uv run test_client.py --product "iPhone 15 Pro"
uv run test_client.py --person "Elon Musk"
uv run test_client.py --api "user authentication"
uv run test_client.py --troubleshoot "computer won't start"
uv run test_client.py --article "artificial intelligence"
```

## Deployment Options

### Local Development
- Use `uv run fastmcp_server.py` for local development and testing
- Configure with Kiro or Q Chat using the `uv` command approach

### Docker Deployment
- Use the provided Dockerfile for containerized deployment
- Suitable for cloud deployment or isolated environments
- Supports environment variable configuration for AWS credentials

### Cloud Deployment
- The Docker image can be deployed to any container platform (ECS, Kubernetes, etc.)
- Configure AWS credentials via environment variables or IAM roles
- The server uses stdio transport, suitable for process-based communication

## License

This project is licensed under the MIT License - see the LICENSE file for details.