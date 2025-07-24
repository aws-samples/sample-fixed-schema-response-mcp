#!/bin/bash
# Setup script for Fixed Schema Response MCP Server (FastMCP Edition)

echo "Setting up Fixed Schema Response MCP Server (FastMCP Edition)..."

# Check if virtual environment already exists
if [ -d "fixed_schema_mcp_venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    # Create virtual environment
    echo "Creating virtual environment..."
    python3 -m venv fixed_schema_mcp_venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source fixed_schema_mcp_venv/bin/activate

# Check if dependencies are already installed
python -c "import mcp.server.fastmcp" 2>/dev/null && {
    echo "Dependencies already installed. Skipping installation."
} || {
    # Install dependencies
    echo "Installing dependencies..."
    pip install fastmcp boto3 jsonschema
}

# Make run script executable
echo "Making run script executable..."
chmod +x fixed_schema_mcp_server/run_fastmcp.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the server:"
echo "  ./fixed_schema_mcp_server/run_fastmcp.sh"
echo ""
echo "To test the server:"
echo "  python fixed_schema_mcp_server/test_client.py --product 'iPhone 15 Pro'"
echo ""
echo "To configure with Kiro, update the path in .kiro/settings/mcp.json to:"
echo "  \"command\": \"$(pwd)/fixed_schema_mcp_server/run_fastmcp.sh\""