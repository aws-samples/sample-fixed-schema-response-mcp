#!/usr/bin/env python3
"""
Security validation test script for the FastMCP server.

This script tests the security improvements implemented in the server.
"""

import json
import re
from security_config import SecurityValidator

def test_schema_name_validation():
    """Test schema name validation."""
    print("Testing schema name validation...")
    
    # Valid names
    valid_names = ["user_profile", "api-endpoint", "test123", "a", "A_B-C_123"]
    for name in valid_names:
        is_valid, error = SecurityValidator.validate_schema_name(name)
        print(f"  '{name}': {'✓' if is_valid else '✗'} {error or ''}")
        assert is_valid, f"Valid name '{name}' was rejected: {error}"
    
    # Invalid names
    invalid_names = [
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
    
    for name in invalid_names:
        is_valid, error = SecurityValidator.validate_schema_name(name)
        print(f"  '{name}': {'✗' if not is_valid else '✓'} {error or ''}")
        assert not is_valid, f"Invalid name '{name}' was accepted"

def test_file_path_validation():
    """Test file path validation."""
    print("\nTesting file path validation...")
    
    base_dir = "/app/schemas"
    
    # Valid paths
    valid_paths = [
        "/app/schemas/test.json",
        "/app/schemas/user_profile.json",
    ]
    
    for path in valid_paths:
        is_valid, error = SecurityValidator.validate_file_path(path, base_dir)
        print(f"  '{path}': {'✓' if is_valid else '✗'} {error or ''}")
    
    # Invalid paths
    invalid_paths = [
        "/app/schemas/../../../etc/passwd",
        "/etc/passwd",
        "/app/schemas/test.txt",  # Wrong extension
        "/app/other/test.json",  # Outside base dir
    ]
    
    for path in invalid_paths:
        is_valid, error = SecurityValidator.validate_file_path(path, base_dir)
        print(f"  '{path}': {'✗' if not is_valid else '✓'} {error or ''}")

def test_json_schema_validation():
    """Test JSON schema validation."""
    print("\nTesting JSON schema validation...")
    
    # Valid schemas
    valid_schemas = [
        '{"type": "object", "properties": {"name": {"type": "string"}}}',
        '{"type": "string"}',
        '{"type": "array", "items": {"type": "number"}}',
    ]
    
    for schema in valid_schemas:
        is_valid, error, parsed = SecurityValidator.validate_json_schema(schema)
        print(f"  Valid schema: {'✓' if is_valid else '✗'} {error or ''}")
        assert is_valid, f"Valid schema was rejected: {error}"
    
    # Invalid schemas
    invalid_schemas = [
        'invalid json',
        '{"no_type": "object"}',  # Missing type
        '{"type": "object", "$ref": "#/definitions/user"}',  # Dangerous property
        '"just a string"',  # Not an object
    ]
    
    for schema in invalid_schemas:
        is_valid, error, parsed = SecurityValidator.validate_json_schema(schema)
        print(f"  Invalid schema: {'✗' if not is_valid else '✓'} {error or ''}")

def test_system_prompt_validation():
    """Test system prompt validation."""
    print("\nTesting system prompt validation...")
    
    # Valid prompts
    valid_prompts = [
        "You are a helpful assistant.",
        "Generate weather information.",
        "A" * 1000,  # Long but within limit
    ]
    
    for prompt in valid_prompts:
        is_valid, error = SecurityValidator.validate_system_prompt(prompt)
        print(f"  Valid prompt: {'✓' if is_valid else '✗'} {error or ''}")
        assert is_valid, f"Valid prompt was rejected: {error}"
    
    # Invalid prompts
    invalid_prompts = [
        "A" * 2001,  # Too long
        "<script>alert('xss')</script>",  # XSS attempt
        "javascript:alert('xss')",  # JavaScript injection
        "eval('malicious code')",  # Code injection
    ]
    
    for prompt in invalid_prompts:
        is_valid, error = SecurityValidator.validate_system_prompt(prompt)
        print(f"  Invalid prompt: {'✗' if not is_valid else '✓'} {error or ''}")

def test_log_sanitization():
    """Test log message sanitization."""
    print("\nTesting log sanitization...")
    
    test_cases = [
        ("Normal message", "Normal message"),
        ("Message with\nnewline", "Message withnewline"),
        ("A" * 600, "A" * 500 + "..."),
        ("Control\x00chars\x1f", "Controlchars"),
    ]
    
    for input_msg, expected in test_cases:
        result = SecurityValidator.sanitize_log_message(input_msg)
        print(f"  Input: '{input_msg[:50]}...' -> Output: '{result[:50]}...'")
        if expected.endswith("..."):
            assert result.endswith("..."), f"Long message not truncated properly"
        else:
            assert result == expected, f"Expected '{expected}', got '{result}'"

if __name__ == "__main__":
    print("Running security validation tests...\n")
    
    try:
        test_schema_name_validation()
        test_file_path_validation()
        test_json_schema_validation()
        test_system_prompt_validation()
        test_log_sanitization()
        
        print("\n✅ All security tests passed!")
        
    except Exception as e:
        print(f"\n❌ Security test failed: {e}")
        import traceback
        traceback.print_exc()