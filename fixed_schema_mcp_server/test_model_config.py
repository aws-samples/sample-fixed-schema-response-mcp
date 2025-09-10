#!/usr/bin/env python3
"""
Test script for model configuration functionality.
"""

import json
import sys
import os

# Add the server directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import fastmcp_server

def test_model_config():
    """Test the model configuration tools."""
    print("Testing model configuration tools...")
    
    # Test get_model_config
    print("\n1. Getting current model config:")
    config = fastmcp_server.get_model_config()
    print(json.dumps(config, indent=2))
    
    # Test available providers
    print("\n2. Available providers:")
    available = config.get("available_providers", {})
    for provider, info in available.items():
        print(f"  {provider}: {info.get('models', [])}")
    
    print("\n3. Current configuration:")
    current = config.get("current_config", {})
    print(f"  Provider: {current.get('provider')}")
    print(f"  Model ID: {current.get('model_id')}")
    print(f"  Credentials configured: {current.get('credentials_configured')}")
    
    print("\nModel configuration test completed successfully!")

if __name__ == "__main__":
    test_model_config()