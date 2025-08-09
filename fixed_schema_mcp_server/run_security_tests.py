#!/usr/bin/env python3
"""
Comprehensive security test runner for the FastMCP server.

This script runs security tests against the actual MCP server to validate
that security improvements are working correctly.
"""

import json
import subprocess
import sys
import os
from typing import Dict, Any, Optional

def send_mcp_request(tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Send a request to the MCP server and return the response."""
    request = {
        "id": "security-test",
        "name": tool_name,
        "args": params
    }
    
    request_json = json.dumps(request)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, "fastmcp_server.py")
    
    server_process = subprocess.Popen(
        [sys.executable, server_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        server_process.stdin.write(request_json + "\n")
        server_process.stdin.flush()
        response_line = server_process.stdout.readline().strip()
        
        try:
            return json.loads(response_line)
        except json.JSONDecodeError:
            return None
    finally:
        server_process.terminate()
        server_process.wait()

def test_malicious_schema_names():
    """Test that malicious schema names are rejected."""
    print("🔒 Testing malicious schema names...")
    
    malicious_names = [
        "../../../malicious",
        "test@schema",
        "schema with spaces",
        "schema/with/slashes",
        "schema\\with\\backslashes",
        "a" * 51,  # Too long
        "",  # Empty
        "admin",  # Reserved
        "system",  # Reserved
    ]
    
    valid_schema = '{"type": "object", "properties": {"test": {"type": "string"}}}'
    
    for name in malicious_names:
        response = send_mcp_request("add_schema", {
            "schema_name": name,
            "schema_definition": valid_schema,
            "description": "Test schema"
        })
        
        if response and response.get("status") == "error":
            print(f"  ✅ Correctly rejected: '{name}' - {response.get('message', '')}")
        else:
            print(f"  ❌ SECURITY ISSUE: Accepted malicious name: '{name}'")
            return False
    
    return True

def test_malicious_json_schemas():
    """Test that malicious JSON schemas are rejected."""
    print("\n🔒 Testing malicious JSON schemas...")
    
    malicious_schemas = [
        'invalid json',
        '{"no_type": "object"}',  # Missing type
        '{"type": "object", "$ref": "#/definitions/user"}',  # Dangerous property
        '"just a string"',  # Not an object
        '{"type": "object", "allOf": [{"type": "string"}]}',  # Dangerous property
    ]
    
    for schema in malicious_schemas:
        response = send_mcp_request("add_schema", {
            "schema_name": "test_schema",
            "schema_definition": schema,
            "description": "Test schema"
        })
        
        if response and response.get("status") == "error":
            print(f"  ✅ Correctly rejected malicious schema: {response.get('message', '')}")
        else:
            print(f"  ❌ SECURITY ISSUE: Accepted malicious schema")
            return False
    
    return True

def test_malicious_system_prompts():
    """Test that malicious system prompts are rejected."""
    print("\n🔒 Testing malicious system prompts...")
    
    malicious_prompts = [
        "A" * 2001,  # Too long
        "<script>alert('xss')</script>",  # XSS attempt
        "javascript:alert('xss')",  # JavaScript injection
        "eval('malicious code')",  # Code injection
    ]
    
    valid_schema = '{"type": "object", "properties": {"test": {"type": "string"}}}'
    
    for prompt in malicious_prompts:
        response = send_mcp_request("add_schema", {
            "schema_name": "test_prompt",
            "schema_definition": valid_schema,
            "description": "Test schema",
            "system_prompt": prompt
        })
        
        if response and response.get("status") == "error":
            print(f"  ✅ Correctly rejected malicious prompt: {response.get('message', '')}")
        else:
            print(f"  ❌ SECURITY ISSUE: Accepted malicious system prompt")
            return False
    
    return True

def test_valid_schema_creation():
    """Test that valid schemas are accepted."""
    print("\n✅ Testing valid schema creation...")
    
    response = send_mcp_request("add_schema", {
        "schema_name": "security_test_valid",
        "schema_definition": '{"type": "object", "properties": {"name": {"type": "string"}, "value": {"type": "number"}}}',
        "description": "Valid test schema for security testing",
        "system_prompt": "You are a helpful assistant providing structured data."
    })
    
    if response and response.get("status") == "success":
        print(f"  ✅ Valid schema accepted: {response.get('message', '')}")
        return True
    else:
        print(f"  ❌ Valid schema rejected: {response}")
        return False

def cleanup_test_files():
    """Clean up test schema files created during testing."""
    print("\n🧹 Cleaning up test files...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schemas_dir = os.path.join(script_dir, "test_config", "schemas")
    
    test_files = [
        "security_test_valid.json",
        "test_schema.json",
        "test_prompt.json",
    ]
    
    for filename in test_files:
        file_path = os.path.join(schemas_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"  ✅ Removed: {filename}")
            except Exception as e:
                print(f"  ⚠️  Failed to remove {filename}: {e}")

def main():
    """Run all security tests."""
    print("🛡️  Running comprehensive security tests for FastMCP server...\n")
    
    all_passed = True
    
    # Run security tests
    tests = [
        test_malicious_schema_names,
        test_malicious_json_schemas,
        test_malicious_system_prompts,
        test_valid_schema_creation,
    ]
    
    for test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            all_passed = False
    
    # Cleanup
    cleanup_test_files()
    
    # Final result
    if all_passed:
        print("\n🎉 All security tests passed! The server is secure.")
    else:
        print("\n⚠️  Some security tests failed. Please review the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)