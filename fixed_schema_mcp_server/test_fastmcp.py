#!/usr/bin/env python3
"""
Test script for the Fixed Schema Response MCP Server (FastMCP Edition).

This script tests the FastMCP server by sending requests to each of the available tools.
"""

import json
import os
import sys
import subprocess
import time
from typing import Dict, Any

def run_test(tool_name: str, params: Dict[str, Any]) -> None:
    """
    Run a test for a specific tool.
    
    Args:
        tool_name: The name of the tool to test
        params: The parameters to pass to the tool
    """
    print(f"\n=== Testing {tool_name} ===")
    
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
            print(f"Response: {json.dumps(response, indent=2)}")
            
            # Check if the response is valid
            if "error" in response:
                print(f"Error: {response['error']}")
            else:
                print("Test passed!")
                
        except json.JSONDecodeError:
            print(f"Failed to parse response as JSON: {response_line}")
            
    finally:
        # Terminate the server
        server_process.terminate()
        server_process.wait()

def main() -> None:
    """
    Run tests for all tools.
    """
    print("Testing Fixed Schema Response MCP Server (FastMCP Edition)")
    
    # Test get_product_info
    run_test("get_product_info", {"product_name": "iPhone 15 Pro"})
    
    # Test get_person_profile
    run_test("get_person_profile", {"person_name": "Elon Musk"})
    
    # Test get_api_endpoint
    run_test("get_api_endpoint", {"endpoint_name": "user authentication"})
    
    # Test get_troubleshooting_guide
    run_test("get_troubleshooting_guide", {"issue": "computer won't start"})
    
    # Test get_article_summary
    run_test("get_article_summary", {"topic": "artificial intelligence"})
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()