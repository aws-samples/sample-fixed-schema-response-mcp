#!/usr/bin/env python3
"""
Test client for the Fixed Schema Response MCP Server (FastMCP Edition).

This script tests the FastMCP server by sending requests to each of the available tools.
It uses subprocess to communicate with the server directly.
"""

import json
import os
import sys
import subprocess
import argparse
from typing import Dict, Any, Optional

def send_request(tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Send a request to the FastMCP server.
    
    Args:
        tool_name: The name of the tool to invoke
        params: The parameters to pass to the tool
        
    Returns:
        The response from the server, or None if an error occurred
    """
    # Create the request
    request = {
        "id": "test-request",
        "name": tool_name,
        "args": params
    }
    
    # Convert the request to JSON
    request_json = json.dumps(request)
    
    # Create the command to run the server
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, "fastmcp_server.py")
    
    # Start the server
    server_process = subprocess.Popen(
        [sys.executable, server_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send the request to the server
        print(f"Sending request: {request_json}")
        server_process.stdin.write(request_json + "\n")
        server_process.stdin.flush()
        
        # Wait for the response
        response_line = server_process.stdout.readline().strip()
        
        # Parse the response
        try:
            response = json.loads(response_line)
            return response
        except json.JSONDecodeError:
            print(f"Failed to parse response as JSON: {response_line}")
            return None
            
    finally:
        # Terminate the server
        server_process.terminate()
        server_process.wait()

def main():
    """Run the test client."""
    parser = argparse.ArgumentParser(description="Test client for Fixed Schema MCP Server (FastMCP Edition)")
    parser.add_argument("--product", help="Get product information")
    parser.add_argument("--person", help="Get person profile")
    parser.add_argument("--api", help="Get API endpoint documentation")
    parser.add_argument("--troubleshoot", help="Get troubleshooting guide")
    parser.add_argument("--article", help="Get article summary")
    
    args = parser.parse_args()
    
    if args.product:
        print(f"Getting product information for: {args.product}")
        response = send_request("get_product_info", {"product_name": args.product})
    elif args.person:
        print(f"Getting person profile for: {args.person}")
        response = send_request("get_person_profile", {"person_name": args.person})
    elif args.api:
        print(f"Getting API endpoint documentation for: {args.api}")
        response = send_request("get_api_endpoint", {"endpoint_name": args.api})
    elif args.troubleshoot:
        print(f"Getting troubleshooting guide for: {args.troubleshoot}")
        response = send_request("get_troubleshooting_guide", {"issue": args.troubleshoot})
    elif args.article:
        print(f"Getting article summary for: {args.article}")
        response = send_request("get_article_summary", {"topic": args.article})
    else:
        parser.print_help()
        return
    
    if response:
        print("\nResponse:")
        print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main()