---
inclusion: always
---

# Project Structure Guide

This steering file provides comprehensive guidance for working with the JSON Schema MCP Server project structure and development practices.

## Project Overview

This is a Model Context Protocol (MCP) server that dynamically loads JSON schemas and generates structured responses using FastMCP and AWS Bedrock Claude. The project is designed to be completely extensible without code changes.

## Directory Structure

### Root Level
- `README.md` - Main project documentation and quick start guide
- `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` - Standard open source project files
- `.gitignore` - Git ignore patterns for Python, virtual environments, and IDE files

### Core Server (`fixed_schema_mcp_server/`)
- `fastmcp_server.py` - Main FastMCP server implementation
- `pyproject.toml` - Python project configuration and dependencies
- `uv.lock` - UV package manager lock file
- `README.md` - Detailed server documentation
- `GENERIC_USAGE.md` - Generic usage guide for any MCP client
- `Dockerfile` - Container configuration for deployment

### Documentation (`fixed_schema_mcp_server/docs/`)
- `KIRO_INTEGRATION.md` - Complete Kiro IDE integration guide
- `Q_CHAT_INTEGRATION.md` - Q Chat integration guide
- `ADDING_SCHEMAS.md` - Guide for adding new schemas

### Configuration (`fixed_schema_mcp_server/test_config/`)
- `config.json` - Server configuration file
- `schemas/` - Directory containing all JSON schema files (10 current schemas)

### Testing (`fixed_schema_mcp_server/`)
- `test_fastmcp.py` - FastMCP server tests
- `test_client.py` - Client testing utilities
- `test_schemas.py` - Schema validation tests
- `test_generic_server.py` - Generic server functionality tests
- `demo_add_schema.py` - Demonstration of adding schemas programmatically

### Development Environment
- `fixed_schema_mcp_venv/` - Python virtual environment (closed folder)
- `.pytest_cache/` - Pytest cache directories

### Temporary Files (`temp-stuff/`)
- `AWS_DEPLOYMENT_GUIDE.md` - AWS deployment documentation
- `PRFAQ.md` - Press release FAQ document
- `open-source-ticket.md` - Open source planning document

### Kiro Configuration (`.kiro/`)
- `settings/mcp.json` - MCP server configuration for Kiro
- `steering/` - Steering files for development guidance
- `hooks/` - Agent hooks for automated workflows
- `specs/` - Feature specifications

## Development Practices

### Adding New Schemas
1. Create JSON schema file in `fixed_schema_mcp_server/test_config/schemas/`
2. Use the `add_schema` tool for runtime addition
3. Restart MCP server to load new schemas
4. Test with the generated `get_{schema_name}` tool

### Testing Approach
- Use `test_fastmcp.py` for server functionality
- Use `test_schemas.py` for schema validation
- Use `test_client.py` for client interaction testing
- Run tests with: `cd fixed_schema_mcp_server && python -m pytest`

### Server Development
- Main server logic in `fastmcp_server.py`
- Uses FastMCP framework for MCP protocol implementation
- Integrates with AWS Bedrock Claude for AI responses
- Falls back to mock responses when AWS credentials unavailable

### Configuration Management
- Server config in `test_config/config.json`
- MCP client config in `.kiro/settings/mcp.json`
- Schema files are automatically discovered and loaded

## File Naming Conventions

### Schema Files
- Use snake_case: `weather_report.json`, `api_endpoint.json`
- Include descriptive names that match the tool purpose
- Store in `fixed_schema_mcp_server/test_config/schemas/`

### Test Files
- Prefix with `test_`: `test_fastmcp.py`, `test_schemas.py`
- Group related tests in the same file
- Use descriptive test method names

### Documentation Files
- Use UPPERCASE for major docs: `README.md`, `CONTRIBUTING.md`
- Use descriptive names for guides: `KIRO_INTEGRATION.md`
- Store integration guides in `docs/` subdirectory

## Key Architecture Principles

### Dynamic Schema Loading
- Schemas are loaded automatically from JSON files
- No code changes required to add new tools
- Each schema generates a corresponding `get_{name}` tool

### Extensibility
- Add unlimited schemas without server code changes
- Custom system prompts per schema for specialized AI behavior
- Runtime schema addition with `add_schema` tool

### Integration Flexibility
- Works with any MCP-compatible client
- Specific integration guides for popular clients
- Generic usage patterns for broad compatibility

## Common Development Tasks

### Running the Server
```bash
cd fixed_schema_mcp_server
uv run fastmcp_server.py
```

### Testing Changes
```bash
cd fixed_schema_mcp_server
python -m pytest
```

### Adding a New Schema
1. Create schema JSON file
2. Use `@fixed-schema add_schema` tool
3. Restart server
4. Test new tool

### Updating Documentation
- Update relevant files in `docs/` directory
- Update main `README.md` if architecture changes
- Update steering files for development guidance changes

## Integration Context

This project is designed to work seamlessly with:
- **Kiro IDE**: Full integration with steering files and MCP configuration
- **Q Chat**: Alternative MCP client integration
- **Generic MCP Clients**: Universal compatibility through standard MCP protocol

The current setup includes 10 pre-built schemas covering common use cases like API documentation, recipes, weather reports, and troubleshooting guides, with the ability to add unlimited custom schemas.