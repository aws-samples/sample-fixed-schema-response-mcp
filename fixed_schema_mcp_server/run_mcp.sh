#!/bin/bash
# Run the MCP server using the virtual environment

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
pip install requests

# Start the HTTP server in the background
python "$SCRIPT_DIR/run_server.py" "$@" &
HTTP_SERVER_PID=$!

# Wait for the HTTP server to start
echo "Waiting for HTTP server to start..."
sleep 2

# Run the MCP wrapper
python "$SCRIPT_DIR/mcp_wrapper.py" --host localhost --port 8081

# Kill the HTTP server when the MCP wrapper exits
kill $HTTP_SERVER_PID