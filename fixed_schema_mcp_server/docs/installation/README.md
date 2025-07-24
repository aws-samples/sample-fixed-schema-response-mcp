# Installation and Setup Guide for FastMCP Edition

## Installation

### Prerequisites

Before installing the Fixed Schema Response MCP Server (FastMCP Edition), ensure you have the following prerequisites:

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)
- AWS credentials (optional, for AWS Bedrock integration)
- FastMCP library

### Installation Methods

#### Method 1: Install Dependencies

```bash
pip install fastmcp boto3 jsonschema
```

#### Method 2: Install from Source

To install from source:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fixed-schema-mcp-server.git
   cd fixed-schema-mcp-server
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

## AWS Credentials Configuration (Optional)

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

## Schema Configuration

The server automatically loads schemas from the `test_config/schemas` directory. The following schemas are included:

- `product_info.json`: Schema for product information
- `person_profile.json`: Schema for person profiles
- `api_endpoint.json`: Schema for API endpoint documentation
- `troubleshooting_guide.json`: Schema for troubleshooting guides
- `article_summary.json`: Schema for article summaries

You can modify these schemas or add new ones by creating JSON files in the `test_config/schemas` directory.

## Running the Server

Run the provided script to start the FastMCP server:

```bash
./run_fastmcp.sh
```

## Kiro Integration

The server is already configured for Kiro in `.kiro/settings/mcp.json`. The configuration includes:

```json
{
  "mcpServers": {
    "fixed-schema": {
      "command": "/path/to/fixed_schema_mcp_server/run_fastmcp.sh",
      "args": [],
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

Make sure to update the `command` path to the absolute path of your `run_fastmcp.sh` script.

## Testing the Server

You can test the server using the included test client:

```bash
python test_client.py --product "iPhone 15 Pro"
python test_client.py --person "Elon Musk"
python test_client.py --api "user authentication"
python test_client.py --troubleshoot "computer won't start"
python test_client.py --article "artificial intelligence"
```

## Next Steps

- Learn more about [schema definitions](../schema/README.md)
- Explore the [Kiro integration guide](../kiro_integration.md)
- Check out the [troubleshooting guide](../troubleshooting/README.md) if you encounter issues