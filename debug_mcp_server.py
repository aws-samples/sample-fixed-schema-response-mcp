#!/usr/bin/env python3
"""
Debug script for MCP server.
"""

import json
import sys
import logging
import os
import time
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="mcp_server.log",
    filemode="w"
)

logger = logging.getLogger(__name__)

def main():
    """Run the debug script."""
    # Start the simple_mcp_server.py script
    process = subprocess.Popen(
        ["python3", "simple_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send an initialize request
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "kiro",
                "version": "0.0.0"
            }
        }
    }
    
    logger.info(f"Sending initialize request: {initialize_request}")
    process.stdin.write(json.dumps(initialize_request) + "\n")
    process.stdin.flush()
    
    # Read the response
    initialize_response = process.stdout.readline()
    logger.info(f"Received initialize response: {initialize_response}")
    
    # Send a listTools request
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "listTools",
        "params": {}
    }
    
    logger.info(f"Sending listTools request: {list_tools_request}")
    process.stdin.write(json.dumps(list_tools_request) + "\n")
    process.stdin.flush()
    
    # Read the response
    list_tools_response = process.stdout.readline()
    logger.info(f"Received listTools response: {list_tools_response}")
    
    # Parse the response
    try:
        response = json.loads(list_tools_response)
        tools = response.get("result", {}).get("tools", [])
        logger.info(f"Tools: {tools}")
    except Exception as e:
        logger.error(f"Error parsing listTools response: {e}")
    
    # Send a shutdown request
    shutdown_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "shutdown",
        "params": {}
    }
    
    logger.info(f"Sending shutdown request: {shutdown_request}")
    process.stdin.write(json.dumps(shutdown_request) + "\n")
    process.stdin.flush()
    
    # Read the response
    shutdown_response = process.stdout.readline()
    logger.info(f"Received shutdown response: {shutdown_response}")
    
    # Close the process
    process.stdin.close()
    
    # Wait for the process to finish
    process.wait()
    
    # Read any remaining output from stderr
    stderr = process.stderr.read()
    logger.info(f"Stderr: {stderr}")

if __name__ == "__main__":
    main()