#!/usr/bin/env python3
"""
Setup script for the Fixed Schema Response MCP Server.
"""

from setuptools import setup, find_packages

setup(
    name="fixed-schema-mcp-server",
    version="0.1.0",
    description="A Model Context Protocol server that returns responses in a fixed schema format",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "boto3>=1.28.0",
        "botocore>=1.31.0",
        "jsonschema>=4.0.0",
        "pydantic>=2.0.0",
        "aiohttp>=3.8.0",
    ],
    entry_points={
        "console_scripts": [
            "fixed-schema-mcp-server=fixed_schema_mcp_server.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)