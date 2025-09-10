#!/usr/bin/env python3
"""
Security configuration and utilities for the FastMCP server.

This module provides security-related constants, validation functions,
and best practices for the MCP server implementation.
"""

import re
import os
from typing import Dict, Any, Optional, Tuple

# Security constants
MAX_SCHEMA_NAME_LENGTH = 50
MAX_SYSTEM_PROMPT_LENGTH = 2000
MAX_QUERY_LENGTH = 5000
MAX_RESPONSE_SIZE = 100000  # 100KB
VALID_SCHEMA_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Allowed file extensions for schema files
ALLOWED_SCHEMA_EXTENSIONS = {'.json'}

# Rate limiting (requests per minute)
DEFAULT_RATE_LIMIT = 60

class SecurityValidator:
    """Security validation utilities for the MCP server."""
    
    @staticmethod
    def validate_schema_name(schema_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate schema name for security and format compliance.
        
        Args:
            schema_name: The schema name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not schema_name:
            return False, "Schema name cannot be empty"
        
        if len(schema_name) > MAX_SCHEMA_NAME_LENGTH:
            return False, f"Schema name must be {MAX_SCHEMA_NAME_LENGTH} characters or less"
        
        if not VALID_SCHEMA_NAME_PATTERN.match(schema_name):
            return False, "Schema name must contain only alphanumeric characters, underscores, and hyphens"
        
        # Check for reserved names
        reserved_names = {'admin', 'system', 'config', 'test', 'debug'}
        if schema_name.lower() in reserved_names:
            return False, f"Schema name '{schema_name}' is reserved"
        
        return True, None
    
    @staticmethod
    def validate_file_path(file_path: str, base_dir: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file path to prevent directory traversal attacks.
        
        Args:
            file_path: The file path to validate
            base_dir: The base directory that the file should be within
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Resolve the absolute path
            abs_file_path = os.path.abspath(file_path)
            abs_base_dir = os.path.abspath(base_dir)
            
            # Check if the file path is within the base directory
            if not abs_file_path.startswith(abs_base_dir):
                return False, "File path is outside the allowed directory"
            
            # Check file extension
            _, ext = os.path.splitext(abs_file_path)
            if ext not in ALLOWED_SCHEMA_EXTENSIONS:
                return False, f"File extension '{ext}' is not allowed"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid file path: {str(e)}"
    
    @staticmethod
    def validate_json_schema(schema_definition: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate JSON schema definition.
        
        Args:
            schema_definition: The JSON schema as a string
            
        Returns:
            Tuple of (is_valid, error_message, parsed_schema)
        """
        try:
            import json
            schema_json = json.loads(schema_definition)
            
            # Basic validation
            if not isinstance(schema_json, dict):
                return False, "Schema must be a JSON object", None
            
            if "type" not in schema_json:
                return False, "Schema must have a 'type' field", None
            
            # Check for potentially dangerous schema properties
            dangerous_props = ['$ref', 'allOf', 'anyOf', 'oneOf']
            for prop in dangerous_props:
                if prop in schema_json:
                    return False, f"Schema property '{prop}' is not allowed for security reasons", None
            
            return True, None, schema_json
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}", None
        except Exception as e:
            return False, f"Schema validation error: {str(e)}", None
    
    @staticmethod
    def sanitize_log_message(message: str, max_length: int = 500) -> str:
        """
        Sanitize log messages to prevent log injection and limit size.
        
        Args:
            message: The message to sanitize
            max_length: Maximum length of the sanitized message
            
        Returns:
            Sanitized message
        """
        if not isinstance(message, str):
            message = str(message)
        
        # Remove control characters and newlines
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', message)
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized
    
    @staticmethod
    def validate_system_prompt(system_prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Validate system prompt for security and length.
        
        Args:
            system_prompt: The system prompt to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(system_prompt) > MAX_SYSTEM_PROMPT_LENGTH:
            return False, f"System prompt must be {MAX_SYSTEM_PROMPT_LENGTH} characters or less"
        
        # Check for potentially dangerous content
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'data:text/html',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, system_prompt, re.IGNORECASE):
                return False, "System prompt contains potentially dangerous content"
        
        return True, None

def get_secure_config_defaults() -> Dict[str, Any]:
    """
    Get secure default configuration values.
    
    Returns:
        Dictionary of secure default configuration
    """
    return {
        "security": {
            "max_schema_name_length": MAX_SCHEMA_NAME_LENGTH,
            "max_system_prompt_length": MAX_SYSTEM_PROMPT_LENGTH,
            "max_query_length": MAX_QUERY_LENGTH,
            "max_response_size": MAX_RESPONSE_SIZE,
            "rate_limit_per_minute": DEFAULT_RATE_LIMIT,
            "allowed_schema_extensions": list(ALLOWED_SCHEMA_EXTENSIONS),
            "enable_request_logging": False,  # Disable by default for security
            "enable_response_logging": False,  # Disable by default for security
        },
        "model": {
            "provider": "aws_bedrock",
            "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            "max_tokens": 4096,
            "temperature": 0.2,
            "timeout_seconds": 30,
        }
    }