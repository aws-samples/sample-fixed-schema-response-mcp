#!/bin/bash
# Run the FastMCP server with AWS Bedrock Claude 4 Sonnet

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set up the virtual environment path
VENV_PATH="${SCRIPT_DIR}/../fixed_schema_mcp_venv"

# Check if the virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Install required packages
pip install -e "$SCRIPT_DIR"
pip install fastmcp boto3

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Warning: AWS credentials not found in environment variables."
    echo "The server will fall back to mock responses if AWS credentials are not configured."
    echo "To use AWS Bedrock, please configure your AWS credentials using one of these methods:"
    echo "1. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
    echo "2. Configure credentials in ~/.aws/credentials"
    echo "3. Use an EC2 instance role or container role"
fi

# Run the FastMCP server
echo "Starting FastMCP server with AWS Bedrock Claude 4 Sonnet..."
python "$SCRIPT_DIR/fastmcp_server.py"