---
inclusion: always
---

# Architecture Guide

This steering file defines the architectural patterns, design principles, and data flow for the JSON Schema MCP Server project.

## 1. Project Structure and Folder Organization

### Layered Architecture
```
fixed_schema_mcp_server/
├── fastmcp_server.py          # Application Layer (MCP Protocol + Business Logic)
├── test_config/               # Configuration Layer
│   ├── config.json           # Server configuration
│   └── schemas/              # Schema definitions (Data Layer)
├── docs/                     # Documentation Layer
├── tests/                    # Testing Layer
└── pyproject.toml           # Dependency Management
```

### Separation of Concerns
- **Protocol Layer**: FastMCP handles MCP protocol communication
- **Application Layer**: Core server logic in `fastmcp_server.py`
- **Configuration Layer**: JSON-based configuration and schema definitions
- **Integration Layer**: AWS Bedrock client for AI responses
- **Testing Layer**: Comprehensive test coverage for all components

### File Organization Principles
- **Single Responsibility**: Each schema file defines one domain
- **Convention over Configuration**: Automatic tool generation from schema files
- **Extensibility**: Drop-in schema files without code changes
- **Separation**: Configuration, schemas, and code in distinct directories

## 2. Design Patterns

### Factory Pattern (Dynamic Tool Creation)
```python
def create_schema_tool(schema_name: str, schema_config: Dict[str, Any]) -> Callable:
    """Creates tool functions dynamically from schema definitions"""
```
- **Purpose**: Generate MCP tools dynamically from JSON schemas
- **Benefits**: No code changes needed for new tools
- **Implementation**: Function factory creates closures with schema context

### Strategy Pattern (Response Generation)
```python
def invoke_claude(prompt: str, schema_name: str) -> Dict[str, Any]:
    """AWS Bedrock strategy for AI responses"""

def generate_mock_response(prompt: str, schema_name: str) -> Dict[str, Any]:
    """Fallback strategy for mock responses"""
```
- **Purpose**: Pluggable response generation strategies
- **Benefits**: Graceful degradation when AWS unavailable
- **Implementation**: Runtime strategy selection based on AWS availability

### Template Method Pattern (Schema Processing)
```python
def register_schema_tools():
    """Template method for processing all schemas"""
    for schema_name, schema_config in SCHEMAS.items():
        tool_func = create_schema_tool(schema_name, schema_config)
        mcp.tool()(tool_func)
```
- **Purpose**: Consistent processing of all schema files
- **Benefits**: Uniform tool registration and validation
- **Implementation**: Iterate through schemas with consistent processing

### Decorator Pattern (MCP Tool Registration)
```python
@mcp.tool()
def list_available_schemas() -> Dict[str, Any]:
    """Utility tool decorated for MCP registration"""
```
- **Purpose**: Clean separation of business logic from protocol concerns
- **Benefits**: Declarative tool registration
- **Implementation**: FastMCP decorators handle MCP protocol details

### Builder Pattern (Schema Configuration)
```json
{
  "name": "weather_report",
  "description": "Schema for weather report information",
  "schema": { "type": "object", "properties": {...} },
  "system_prompt": "You are a professional meteorologist..."
}
```
- **Purpose**: Structured schema configuration with optional components
- **Benefits**: Flexible schema definitions with sensible defaults
- **Implementation**: JSON configuration with optional fields

## 3. Component/Module Boundaries

### Core Components

#### Schema Manager
- **Responsibility**: Load, validate, and manage JSON schemas
- **Boundaries**: File system operations, schema validation
- **Interface**: `load_schemas()`, schema file discovery
- **Dependencies**: File system, JSON parsing

#### Tool Factory
- **Responsibility**: Generate MCP tools from schema definitions
- **Boundaries**: Dynamic function creation, MCP registration
- **Interface**: `create_schema_tool()`, `register_schema_tools()`
- **Dependencies**: Schema Manager, MCP framework

#### Response Generator
- **Responsibility**: Generate structured responses using AI or mocks
- **Boundaries**: AWS Bedrock integration, fallback logic
- **Interface**: `invoke_claude()`, `generate_mock_response()`
- **Dependencies**: AWS Bedrock, schema definitions

#### Configuration Manager
- **Responsibility**: Load and manage server configuration
- **Boundaries**: Configuration file parsing, environment setup
- **Interface**: `load_config()`, configuration validation
- **Dependencies**: File system, JSON parsing

#### MCP Protocol Handler
- **Responsibility**: Handle MCP protocol communication
- **Boundaries**: Protocol serialization, tool invocation
- **Interface**: FastMCP decorators and framework
- **Dependencies**: FastMCP framework, registered tools

### Boundary Enforcement Rules

#### Schema Isolation
- Each schema file is self-contained
- No cross-schema dependencies
- Schema changes don't affect other schemas
- Independent tool generation per schema

#### Layer Separation
- Configuration layer doesn't contain business logic
- Application layer doesn't handle protocol details
- Integration layer isolated from core logic
- Testing layer mirrors production structure

#### Dependency Direction
```
MCP Protocol → Application Logic → Response Generation → AWS Bedrock
             ↓                   ↓
        Configuration ←    Schema Management
```

## 4. Data Flow Patterns

### Request Processing Flow
```
1. MCP Client Request
   ↓
2. FastMCP Protocol Handler
   ↓
3. Tool Function (Generated)
   ↓
4. Response Generator (Claude/Mock)
   ↓
5. Schema Validation
   ↓
6. MCP Response
```

### Schema Loading Flow
```
1. Server Startup
   ↓
2. Configuration Loading (config.json)
   ↓
3. Schema Directory Discovery
   ↓
4. Schema File Parsing (*.json)
   ↓
5. Tool Generation (create_schema_tool)
   ↓
6. MCP Registration (@mcp.tool)
   ↓
7. Server Ready
```

### Dynamic Schema Addition Flow
```
1. add_schema Tool Call
   ↓
2. Schema Validation (JSON parsing)
   ↓
3. File Creation (schemas/*.json)
   ↓
4. Response (restart required)
   ↓
5. Server Restart
   ↓
6. New Tool Available
```

### Response Generation Flow
```
1. Tool Invocation (query parameter)
   ↓
2. Prompt Construction (schema + query)
   ↓
3. Strategy Selection (AWS available?)
   ├─ AWS Bedrock Claude
   │  ├─ System Prompt (custom or default)
   │  ├─ API Call (bedrock-runtime)
   │  ├─ JSON Extraction
   │  └─ Validation
   └─ Mock Response Generator
      ├─ Schema Analysis
      ├─ Type-based Generation
      └─ Mock Data Creation
   ↓
4. Structured Response (JSON)
```

### Error Handling Flow
```
1. Error Detection
   ├─ AWS API Errors → Mock Fallback
   ├─ JSON Parse Errors → Mock Fallback
   ├─ Schema Errors → Error Response
   └─ File System Errors → Graceful Degradation
   ↓
2. Logging (structured logging)
   ↓
3. User-Friendly Response
```

## Architectural Principles

### Extensibility First
- New schemas require zero code changes
- Plugin-like architecture for response strategies
- Configuration-driven behavior
- Runtime schema addition capability

### Graceful Degradation
- AWS unavailable → Mock responses
- Schema errors → Fallback behavior
- Missing files → Default configuration
- Network issues → Local processing

### Convention over Configuration
- Schema files automatically discovered
- Tool names generated from schema names
- Default system prompts for schemas without custom ones
- Standard directory structure assumptions

### Separation of Concerns
- Protocol handling separate from business logic
- AI integration isolated from core functionality
- Configuration management centralized
- Testing mirrors production architecture

### Data-Driven Architecture
- Schema definitions drive tool creation
- Configuration files control behavior
- JSON-based everything for transparency
- File-based persistence for schemas

This architecture enables rapid development, easy maintenance, and seamless extensibility while maintaining clear boundaries and predictable data flow patterns.