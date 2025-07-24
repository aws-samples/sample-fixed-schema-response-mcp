#!/usr/bin/env python3
"""
Setup script for the Fixed Schema Response MCP Server (FastMCP Edition).
"""

from setuptools import setup

setup(
    name="fixed-schema-mcp-server",
    version="0.2.0",
    description="A FastMCP server that returns responses in a fixed schema format using AWS Bedrock Claude",
    author="Your Name",
    author_email="your.email@example.com",
    py_modules=["fastmcp_server"],
    install_requires=[
        "fastmcp>=0.1.0",
        "boto3>=1.28.0",
        "botocore>=1.31.0",
        "jsonschema>=4.0.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    include_package_data=True,
    package_data={
        "": ["test_config/schemas/*.json"],
    },
)