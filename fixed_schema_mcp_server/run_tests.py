#!/usr/bin/env python3
"""
Script to run tests for the Fixed Schema Response MCP Server (FastMCP Edition).
"""

import os
import sys

if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run the FastMCP test
    fastmcp_test = os.path.join(script_dir, "test_fastmcp.py")
    if os.path.exists(fastmcp_test):
        print(f"Running FastMCP test: {fastmcp_test}")
        exit_code = os.system(f"python {fastmcp_test}")
        if exit_code != 0:
            print("FastMCP test failed")
            sys.exit(1)
    else:
        print(f"FastMCP test not found: {fastmcp_test}")
        sys.exit(1)
    
    # Run the schema test
    schema_test = os.path.join(script_dir, "test_schemas.py")
    if os.path.exists(schema_test):
        print(f"Running schema test: {schema_test}")
        exit_code = os.system(f"python {schema_test}")
        if exit_code != 0:
            print("Schema test failed")
            sys.exit(1)
    
    print("All tests passed!")
    sys.exit(0)