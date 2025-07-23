#!/usr/bin/env python3
"""
Test script for Content-Length header.
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
    parser = argparse.ArgumentParser(description="Test Content-Length header")
    parser.add_argument("--server", type=str, default="simple_mcp_server.py", help="Path to the MCP server script")
    parser.add_argument("--python", type=str, default="python3", help="Python interpreter to use")
    parser.add_argument("--use-header", action="store_true", help="Use Content-Length header")
    
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
    
    if args.use_header:
        # Use Content-Length header
        request_json = json.dumps(initialize_request)
        header = f"Content-Length: {len(request_json)}\r\n\r\n"
        process.stdin.write(header)
        process.stdin.write(request_json)
    else:
        # Send as a single line
        process.stdin.write(json.dumps(initialize_request) + "\n")
    
    process.stdin.flush()
    
    # Read the response
    if args.use_header:
        # Read the header line
        header = process.stdout.readline().strip()
        logger.info(f"Received header: {header}")
        
        if header.startswith("Content-Length: "):
            # Extract the content length
            content_length = int(header[16:])
            
            # Read the separator line
            separator = process.stdout.readline().strip()
            logger.info(f"Received separator: '{separator}'")
            
            # Read the content
            content = ""
            while len(content) < content_length:
                content += process.stdout.read(1)
            
            logger.info(f"Received initialize response: {content}")
            
            try:
                initialize_response = json.loads(content)
                logger.info(f"Parsed initialize response: {initialize_response}")
            except Exception as e:
                logger.error(f"Error parsing initialize response: {e}")
        else:
            logger.error(f"Invalid header: {header}")
    else:
        # Read a single line
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
    
    if args.use_header:
        # Use Content-Length header
        request_json = json.dumps(list_tools_request)
        header = f"Content-Length: {len(request_json)}\r\n\r\n"
        process.stdin.write(header)
        process.stdin.write(request_json)
    else:
        # Send as a single line
        process.stdin.write(json.dumps(list_tools_request) + "\n")
    
    process.stdin.flush()
    
    # Read the response
    if args.use_header:
        # Read the header line
        header = process.stdout.readline().strip()
        logger.info(f"Received header: {header}")
        
        if header.startswith("Content-Length: "):
            # Extract the content length
            content_length = int(header[16:])
            
            # Read the separator line
            separator = process.stdout.readline().strip()
            logger.info(f"Received separator: '{separator}'")
            
            # Read the content
            content = ""
            while len(content) < content_length:
                content += process.stdout.read(1)
            
            logger.info(f"Received listTools response: {content}")
            
            try:
                list_tools_response = json.loads(content)
                tools = list_tools_response.get("result", {}).get("tools", [])
                logger.info(f"Tools: {tools}")
            except Exception as e:
                logger.error(f"Error parsing listTools response: {e}")
        else:
            logger.error(f"Invalid header: {header}")
    else:
        # Read a single line
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
    
    if args.use_header:
        # Use Content-Length header
        request_json = json.dumps(shutdown_request)
        header = f"Content-Length: {len(request_json)}\r\n\r\n"
        process.stdin.write(header)
        process.stdin.write(request_json)
    else:
        # Send as a single line
        process.stdin.write(json.dumps(shutdown_request) + "\n")
    
    process.stdin.flush()
    
    # Read the response
    if args.use_header:
        # Read the header line
        header = process.stdout.readline().strip()
        logger.info(f"Received header: {header}")
        
        if header.startswith("Content-Length: "):
            # Extract the content length
            content_length = int(header[16:])
            
            # Read the separator line
            separator = process.stdout.readline().strip()
            logger.info(f"Received separator: '{separator}'")
            
            # Read the content
            content = ""
            while len(content) < content_length:
                content += process.stdout.read(1)
            
            logger.info(f"Received shutdown response: {content}")
        else:
            logger.error(f"Invalid header: {header}")
    else:
        # Read a single line
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