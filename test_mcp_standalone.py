#!/usr/bin/env python3
"""
Test script for MCP server.
"""

import json
import sys
import logging
import os
import time
import subprocess
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the test script."""
    parser = argparse.ArgumentParser(description="Test MCP server")
    parser.add_argument("--server", type=str, default="simple_mcp_server.py", help="Path to the MCP server script")
    parser.add_argument("--python", type=str, default="python3", help="Python interpreter to use")
    
    args = parser.parse_args()
    
    # Start the MCP server script
    process = subprocess.Popen(
        [args.python, args.server],
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
        
        # Test each tool
        for tool in tools:
            tool_name = tool.get("name")
            logger.info(f"Testing tool: {tool_name}")
            
            # Send an invoke request
            invoke_request = {
                "jsonrpc": "2.0",
                "id": 100 + tools.index(tool),
                "method": "invoke",
                "params": {
                    "name": tool_name,
                    "parameters": {
                        "query": f"Test query for {tool_name}"
                    }
                }
            }
            
            logger.info(f"Sending invoke request: {invoke_request}")
            process.stdin.write(json.dumps(invoke_request) + "\n")
            process.stdin.flush()
            
            # Read the response
            invoke_response = process.stdout.readline()
            logger.info(f"Received invoke response: {invoke_response}")
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