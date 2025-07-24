#!/bin/bash
# Run the FastMCP server with AWS Bedrock Claude 4 Sonnet

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set up the virtual environment path
VENV_PATH="${SCRIPT_DIR}/../fixed_schema_mcp_venv"

# Check if the virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please run the setup first:"
    echo "  ./setup.sh"
    echo ""
    echo "Or manually:"
    echo "  python3 -m venv fixed_schema_mcp_venv"
    echo "  source fixed_schema_mcp_venv/bin/activate"
    echo "  pip install fastmcp boto3 jsonschema"
    exit 1
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Check if required packages are installed
python -c "import mcp.server.fastmcp" 2>/dev/null || {
    echo "Error: FastMCP not installed. Please run setup first:"
    echo "  ./setup.sh"
    echo ""
    echo "Or manually install dependencies:"
    echo "  source fixed_schema_mcp_venv/bin/activate"
    echo "  pip install fastmcp boto3 jsonschema"
    exit 1
}

# Check AWS credentials (optional)
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Info: AWS credentials not found in environment variables."
    echo "The server will use mock responses. To use AWS Bedrock, configure your AWS credentials:"
    echo "1. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
    echo "2. Configure credentials in ~/.aws/credentials"
    echo "3. Use an EC2 instance role or container role"
    echo ""
fi

# Run the FastMCP server
echo "Starting FastMCP server..."
python "$SCRIPT_DIR/fastmcp_server.py"