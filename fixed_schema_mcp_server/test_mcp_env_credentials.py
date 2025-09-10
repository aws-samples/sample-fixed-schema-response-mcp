#!/usr/bin/env python3
"""
Test script for MCP environment variable credential loading.
"""

import json
import sys
import os

# Add the server directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mcp_env_credentials():
    """Test credential loading from environment variables (as set by MCP config)."""
    print("Testing MCP environment variable credential loading...")
    
    # Simulate MCP setting environment variables
    test_env = {
        "OPENAI_API_KEY": "sk-test-openai-key-from-mcp",
        "ANTHROPIC_API_KEY": "sk-ant-test-anthropic-key-from-mcp",
        "AWS_PROFILE": "test-profile",
        "AWS_REGION": "us-east-1"
    }
    
    # Set environment variables (simulating MCP config)
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)  # Save original
        os.environ[key] = value
        print(f"✓ Set {key}={value}")
    
    # Import and test the server
    print("\n1. Importing server with MCP environment variables...")
    import fastmcp_server
    
    # Test configuration loading
    print("\n2. Testing model configuration:")
    try:
        config = fastmcp_server.get_model_config()
        current_config = config['current_config']
        credentials_configured = current_config['credentials_configured']
        
        print(f"   Current provider: {current_config['provider']}")
        print(f"   Model ID: {current_config['model_id']}")
        print(f"   AWS Bedrock available: {credentials_configured['aws_bedrock']}")
        print(f"   OpenAI available: {credentials_configured['openai']}")
        print(f"   Anthropic available: {credentials_configured['anthropic']}")
        
        # Test that at least one provider is available
        if any(credentials_configured.values()):
            print("✓ At least one provider is properly configured")
        else:
            print("✗ No providers are configured")
            
    except Exception as e:
        print(f"✗ Error testing configuration: {e}")
    
    # Test switching providers
    print("\n3. Testing provider switching:")
    providers_to_test = ["openai", "anthropic", "aws_bedrock"]
    
    for provider in providers_to_test:
        try:
            print(f"\n   Testing {provider}:")
            
            # Update config to use this provider
            result = fastmcp_server.update_model_config(
                provider=provider,
                model_id="test-model",
                temperature=0.3
            )
            
            if result.get("status") == "success":
                print(f"   ✓ {provider} configuration updated successfully")
            else:
                print(f"   ✗ {provider} configuration failed: {result.get('message')}")
                
        except Exception as e:
            print(f"   ✗ Error testing {provider}: {e}")
    
    # Clean up environment variables
    print("\n4. Cleaning up test environment...")
    for key, original_value in original_env.items():
        if original_value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = original_value
    
    print("\n✓ MCP environment credential loading test completed!")

if __name__ == "__main__":
    test_mcp_env_credentials()