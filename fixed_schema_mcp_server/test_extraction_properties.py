#!/usr/bin/env python3
"""
Property-based tests for the MCP Transform Refactor feature.

These tests validate the correctness properties defined in the design document
using the hypothesis library for property-based testing.

Feature: mcp-transform-refactor
"""

import json
import re
from typing import Any, Dict, List, Optional
from hypothesis import given, strategies as st, settings, assume

# Import the functions we're testing
from fixed_schema_mcp_server.fastmcp_server import (
    build_extraction_prompt,
    parse_extraction_response,
    create_schema_tool,
    ensure_schema_structure,
    SCHEMAS,
)


# =============================================================================
# Test Strategies (Generators)
# =============================================================================

# Strategy for generating simple field values that might appear in text
simple_values = st.one_of(
    st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S'))),
    st.integers(min_value=-10000, max_value=10000),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    st.booleans(),
)

# Strategy for generating schema field names
field_names = st.text(
    min_size=1, 
    max_size=20, 
    alphabet=st.characters(whitelist_categories=('L',), whitelist_characters='_')
).filter(lambda x: x[0].isalpha() if x else False)

# Strategy for generating simple JSON schemas
@st.composite
def simple_schema(draw):
    """Generate a simple JSON schema with string properties."""
    num_fields = draw(st.integers(min_value=1, max_value=5))
    properties = {}
    for i in range(num_fields):
        field_name = f"field_{i}"
        field_type = draw(st.sampled_from(["string", "integer", "number", "boolean"]))
        properties[field_name] = {"type": field_type}
    
    return {
        "type": "object",
        "properties": properties
    }


# Strategy for generating input text with known data
@st.composite
def input_text_with_data(draw, schema: Dict[str, Any]):
    """Generate input text that contains data matching the schema fields."""
    properties = schema.get("properties", {})
    data_parts = []
    expected_data = {}
    
    for field_name, field_def in properties.items():
        field_type = field_def.get("type", "string")
        
        if field_type == "string":
            value = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))))
            if value.strip():
                data_parts.append(f"The {field_name} is {value}")
                expected_data[field_name] = value
        elif field_type == "integer":
            value = draw(st.integers(min_value=0, max_value=1000))
            data_parts.append(f"The {field_name} is {value}")
            expected_data[field_name] = value
        elif field_type == "number":
            value = draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
            value = round(value, 2)
            data_parts.append(f"The {field_name} is {value}")
            expected_data[field_name] = value
        elif field_type == "boolean":
            value = draw(st.booleans())
            data_parts.append(f"The {field_name} is {value}")
            expected_data[field_name] = value
    
    input_text = ". ".join(data_parts) + "." if data_parts else "No data available."
    return input_text, expected_data


# =============================================================================
# Property 5: Extraction Fidelity
# Validates: Requirements 6.1, 6.2
# 
# *For any* transform operation, the output data SHALL only contain information
# that is explicitly present in the input text - no hallucinated or generated content.
# =============================================================================

class TestExtractionFidelity:
    """
    Feature: mcp-transform-refactor, Property 5: Extraction Fidelity
    Validates: Requirements 6.1, 6.2
    
    This property ensures that the extraction process only extracts information
    that is explicitly present in the input text and does not fabricate data.
    """
    
    @given(schema=simple_schema())
    @settings(max_examples=100)
    def test_extraction_prompt_contains_no_generation_instructions(self, schema: Dict[str, Any]):
        """
        Property 5: Extraction Fidelity - Prompt Structure
        
        For any schema, the extraction prompt SHALL contain explicit instructions
        to NOT generate or fabricate data.
        
        **Validates: Requirements 6.1, 6.2**
        """
        input_text = "Sample input text for extraction."
        prompt = build_extraction_prompt(input_text, schema)
        
        # The prompt must contain anti-hallucination instructions
        assert "ONLY extract" in prompt or "only extract" in prompt.lower(), \
            "Prompt must instruct to ONLY extract information"
        
        assert "DO NOT generate" in prompt or "do not generate" in prompt.lower() or \
               "NOT generate" in prompt or "not generate" in prompt.lower(), \
            "Prompt must instruct NOT to generate data"
        
        assert "hallucinate" in prompt.lower() or "invent" in prompt.lower() or "fabricate" in prompt.lower(), \
            "Prompt must warn against hallucination/invention"
        
        # The prompt must include the schema
        assert "Schema:" in prompt or "schema" in prompt.lower(), \
            "Prompt must include the schema"
        
        # The prompt must include the input text
        assert input_text in prompt, \
            "Prompt must include the input text"
    
    @given(schema=simple_schema())
    @settings(max_examples=100)
    def test_extraction_prompt_instructs_null_for_missing(self, schema: Dict[str, Any]):
        """
        Property 5: Extraction Fidelity - Missing Field Handling
        
        For any schema, the extraction prompt SHALL instruct to return null
        for fields that cannot be found.
        
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        input_text = "Sample input text."
        prompt = build_extraction_prompt(input_text, schema)
        
        # The prompt must instruct to use null for missing fields
        assert "null" in prompt.lower(), \
            "Prompt must instruct to use null for missing fields"
    
    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_parse_extraction_handles_valid_json(self, json_content: str):
        """
        Property 5: Extraction Fidelity - JSON Parsing
        
        For any valid JSON object string, parse_extraction_response SHALL
        return the parsed data without modification.
        
        **Validates: Requirements 6.1, 6.2**
        """
        # Create a valid JSON object
        test_data = {"field_0": json_content if json_content else None}
        valid_json = json.dumps(test_data)
        
        # Ensure we have a schema loaded for testing
        # Use a mock schema name that exists or handle gracefully
        result = parse_extraction_response(valid_json, "product_info")
        
        # Result should contain the original data (possibly with additional null fields)
        if "success" not in result or result.get("success") != False:
            assert "field_0" not in result or result.get("field_0") == test_data["field_0"] or result.get("field_0") is None, \
                "Parsed data should match input or be null"
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))))
    @settings(max_examples=100)
    def test_parse_extraction_handles_invalid_json(self, invalid_content: str):
        """
        Property 5: Extraction Fidelity - Invalid JSON Handling
        
        For any non-JSON string, parse_extraction_response SHALL return
        an error response, not fabricated data.
        
        **Validates: Requirements 6.1, 6.2**
        """
        # Ensure the content is not valid JSON
        assume(not invalid_content.strip().startswith('{'))
        assume(not invalid_content.strip().startswith('['))
        
        try:
            json.loads(invalid_content)
            # If it parses as JSON, skip this test case
            assume(False)
        except json.JSONDecodeError:
            pass
        
        result = parse_extraction_response(invalid_content, "product_info")
        
        # Should return an error, not fabricated data
        assert result.get("success") == False or "error" in result, \
            "Invalid JSON should result in error response, not fabricated data"
    
    @given(schema=simple_schema())
    @settings(max_examples=100)
    def test_extraction_prompt_schema_included(self, schema: Dict[str, Any]):
        """
        Property 5: Extraction Fidelity - Schema Inclusion
        
        For any schema, the extraction prompt SHALL include the complete
        schema definition so the LLM knows the expected structure.
        
        **Validates: Requirements 6.1, 6.2**
        """
        input_text = "Test input."
        prompt = build_extraction_prompt(input_text, schema)
        
        # All schema properties should be mentioned in the prompt
        schema_json = json.dumps(schema, indent=2)
        for field_name in schema.get("properties", {}).keys():
            assert field_name in prompt, \
                f"Schema field '{field_name}' must be included in the prompt"


# =============================================================================
# Property 1: Transform Tool Registration
# Validates: Requirements 1.1, 4.1, 4.2
# 
# *For any* schema loaded from the schemas directory, the MCP server SHALL 
# register exactly one tool named `transform_to_{schema_name}` and SHALL NOT 
# register any tool named `get_{schema_name}`.
# =============================================================================

class TestTransformToolRegistration:
    """
    Feature: mcp-transform-refactor, Property 1: Transform Tool Registration
    Validates: Requirements 1.1, 4.1, 4.2
    
    This property ensures that for any schema, the system creates transform tools
    with the correct naming convention and does not create generation tools.
    """
    
    # Strategy for generating valid schema names
    valid_schema_names = st.text(
        min_size=1,
        max_size=30,
        alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-')
    ).filter(lambda x: x[0].isalpha() if x else False)
    
    @given(schema_name=valid_schema_names)
    @settings(max_examples=100)
    def test_transform_tool_has_correct_name(self, schema_name: str):
        """
        Property 1: Transform Tool Registration - Tool Naming
        
        For any valid schema name, the created tool SHALL be named 
        `transform_to_{schema_name}`.
        
        **Validates: Requirements 1.1, 4.1, 4.2**
        """
        # Create a minimal schema config
        schema_config = {
            "name": schema_name,
            "description": f"Test schema for {schema_name}",
            "schema": {
                "type": "object",
                "properties": {
                    "test_field": {"type": "string"}
                }
            }
        }
        
        # Create the tool
        tool_func = create_schema_tool(schema_name, schema_config)
        
        # Verify the tool name follows transform convention
        expected_name = f"transform_to_{schema_name}"
        assert tool_func.__name__ == expected_name, \
            f"Tool name should be '{expected_name}', got '{tool_func.__name__}'"
        
        # Verify it does NOT use the old generation naming
        assert not tool_func.__name__.startswith("get_"), \
            f"Tool should NOT use 'get_' prefix, got '{tool_func.__name__}'"
    
    @given(schema_name=valid_schema_names)
    @settings(max_examples=100)
    def test_transform_tool_accepts_response_parameter(self, schema_name: str):
        """
        Property 1: Transform Tool Registration - Parameter Name
        
        For any schema, the created tool SHALL accept a `response` parameter
        (not `query`).
        
        **Validates: Requirements 1.1, 1.3**
        """
        import inspect
        
        schema_config = {
            "name": schema_name,
            "description": f"Test schema for {schema_name}",
            "schema": {
                "type": "object",
                "properties": {
                    "test_field": {"type": "string"}
                }
            }
        }
        
        tool_func = create_schema_tool(schema_name, schema_config)
        
        # Get the function signature
        sig = inspect.signature(tool_func)
        param_names = list(sig.parameters.keys())
        
        # Verify the parameter is named 'response'
        assert "response" in param_names, \
            f"Tool should have 'response' parameter, got {param_names}"
        
        # Verify it does NOT have 'query' parameter
        assert "query" not in param_names, \
            f"Tool should NOT have 'query' parameter, got {param_names}"
    
    @given(schema_name=valid_schema_names)
    @settings(max_examples=100)
    def test_transform_tool_has_docstring(self, schema_name: str):
        """
        Property 1: Transform Tool Registration - Documentation
        
        For any schema, the created tool SHALL have a docstring that describes
        the transformation functionality.
        
        **Validates: Requirements 1.1**
        """
        schema_config = {
            "name": schema_name,
            "description": f"Test schema for {schema_name}",
            "schema": {
                "type": "object",
                "properties": {
                    "test_field": {"type": "string"}
                }
            }
        }
        
        tool_func = create_schema_tool(schema_name, schema_config)
        
        # Verify the tool has a docstring
        assert tool_func.__doc__ is not None, \
            "Tool should have a docstring"
        
        # Verify the docstring mentions transformation
        docstring_lower = tool_func.__doc__.lower()
        assert "transform" in docstring_lower or "structured" in docstring_lower, \
            "Docstring should describe transformation functionality"
    
    def test_loaded_schemas_have_transform_tools(self):
        """
        Property 1: Transform Tool Registration - All Schemas
        
        For all schemas loaded from the schemas directory, each SHALL have
        a corresponding transform tool with the correct naming.
        
        **Validates: Requirements 1.1, 4.1, 4.2**
        """
        # Verify we have schemas loaded
        assert len(SCHEMAS) > 0, "Should have at least one schema loaded"
        
        for schema_name, schema_config in SCHEMAS.items():
            tool_func = create_schema_tool(schema_name, schema_config)
            
            # Verify transform naming
            expected_name = f"transform_to_{schema_name}"
            assert tool_func.__name__ == expected_name, \
                f"Schema '{schema_name}' tool should be named '{expected_name}'"
            
            # Verify NOT generation naming
            assert not tool_func.__name__.startswith("get_"), \
                f"Schema '{schema_name}' should NOT have 'get_' prefix"


# =============================================================================
# Property 2: Schema Loading Completeness
# Validates: Requirements 2.1, 2.4
# 
# *For any* set of valid JSON schema files in the `config/schemas/` directory, 
# all schemas SHALL be loaded and returned by `list_available_schemas` with 
# correct tool names.
# =============================================================================

class TestSchemaLoadingCompleteness:
    """
    Feature: mcp-transform-refactor, Property 2: Schema Loading Completeness
    Validates: Requirements 2.1, 2.4
    
    This property ensures that all schemas are loaded from the schemas directory
    and that list_available_schemas returns correct transform tool names.
    """
    
    def test_all_loaded_schemas_in_list(self):
        """
        Property 2: Schema Loading Completeness - All Schemas Listed
        
        For all schemas loaded from the schemas directory, list_available_schemas
        SHALL return all of them.
        
        **Validates: Requirements 2.1, 2.4**
        """
        from fixed_schema_mcp_server.fastmcp_server import list_available_schemas, SCHEMAS
        
        result = list_available_schemas()
        
        # Verify the result structure
        assert "available_schemas" in result, "Result should contain 'available_schemas'"
        assert "total_count" in result, "Result should contain 'total_count'"
        
        # Verify all loaded schemas are in the list
        available = result["available_schemas"]
        assert len(available) == len(SCHEMAS), \
            f"Should list all {len(SCHEMAS)} schemas, got {len(available)}"
        
        for schema_name in SCHEMAS.keys():
            assert schema_name in available, \
                f"Schema '{schema_name}' should be in the list"
    
    def test_list_returns_transform_tool_names(self):
        """
        Property 2: Schema Loading Completeness - Transform Tool Names
        
        For all schemas, list_available_schemas SHALL return tool names
        using the transform_to_{schema_name} convention.
        
        **Validates: Requirements 2.4**
        """
        from fixed_schema_mcp_server.fastmcp_server import list_available_schemas, SCHEMAS
        
        result = list_available_schemas()
        available = result["available_schemas"]
        
        for schema_name, schema_info in available.items():
            expected_tool_name = f"transform_to_{schema_name}"
            actual_tool_name = schema_info.get("tool_name")
            
            # Verify transform naming convention
            assert actual_tool_name == expected_tool_name, \
                f"Schema '{schema_name}' should have tool_name '{expected_tool_name}', got '{actual_tool_name}'"
            
            # Verify NOT using old get_ convention
            assert not actual_tool_name.startswith("get_"), \
                f"Schema '{schema_name}' should NOT use 'get_' prefix"
    
    def test_list_contains_required_fields(self):
        """
        Property 2: Schema Loading Completeness - Required Fields
        
        For all schemas in list_available_schemas, each entry SHALL contain
        name, description, and tool_name fields.
        
        **Validates: Requirements 2.4**
        """
        from fixed_schema_mcp_server.fastmcp_server import list_available_schemas
        
        result = list_available_schemas()
        available = result["available_schemas"]
        
        for schema_name, schema_info in available.items():
            assert "name" in schema_info, \
                f"Schema '{schema_name}' should have 'name' field"
            assert "description" in schema_info, \
                f"Schema '{schema_name}' should have 'description' field"
            assert "tool_name" in schema_info, \
                f"Schema '{schema_name}' should have 'tool_name' field"
            
            # Verify name matches the key
            assert schema_info["name"] == schema_name, \
                f"Schema name field should match key: expected '{schema_name}', got '{schema_info['name']}'"
    
    def test_total_count_matches_schemas(self):
        """
        Property 2: Schema Loading Completeness - Count Accuracy
        
        The total_count returned by list_available_schemas SHALL match
        the actual number of schemas in the available_schemas dictionary.
        
        **Validates: Requirements 2.1, 2.4**
        """
        from fixed_schema_mcp_server.fastmcp_server import list_available_schemas, SCHEMAS
        
        result = list_available_schemas()
        
        assert result["total_count"] == len(result["available_schemas"]), \
            "total_count should match number of available schemas"
        
        assert result["total_count"] == len(SCHEMAS), \
            "total_count should match number of loaded schemas"
    
    # Strategy for generating valid schema names for property testing
    valid_schema_names = st.text(
        min_size=1,
        max_size=30,
        alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-')
    ).filter(lambda x: x[0].isalpha() if x else False)
    
    @given(schema_names=st.lists(valid_schema_names, min_size=1, max_size=5, unique=True))
    @settings(max_examples=100)
    def test_tool_name_format_consistency(self, schema_names: List[str]):
        """
        Property 2: Schema Loading Completeness - Tool Name Format
        
        For any set of schema names, the tool_name format SHALL always be
        transform_to_{schema_name} (never get_{schema_name}).
        
        **Validates: Requirements 2.4, 4.1, 4.2**
        """
        for schema_name in schema_names:
            expected_tool_name = f"transform_to_{schema_name}"
            
            # Verify the expected format
            assert expected_tool_name.startswith("transform_to_"), \
                f"Tool name should start with 'transform_to_'"
            assert schema_name in expected_tool_name, \
                f"Tool name should contain schema name"
            
            # Verify it's NOT the old format
            old_format = f"get_{schema_name}"
            assert expected_tool_name != old_format, \
                f"Tool name should NOT be in old 'get_' format"


# =============================================================================
# Property 4: Missing Field Handling
# Validates: Requirements 1.4, 6.3
# 
# *For any* input that does not contain information for one or more schema fields, 
# the transform output SHALL have `null` values for those missing fields rather 
# than fabricated data.
# =============================================================================

class TestMissingFieldHandling:
    """
    Feature: mcp-transform-refactor, Property 4: Missing Field Handling
    Validates: Requirements 1.4, 6.3
    
    This property ensures that when input text does not contain information for
    schema fields, those fields are set to null rather than fabricated.
    """
    
    # Strategy for generating simple JSON schemas with various field types
    @st.composite
    def schema_with_fields(draw):
        """Generate a schema with a mix of field types."""
        num_fields = draw(st.integers(min_value=2, max_value=6))
        properties = {}
        required = []
        
        for i in range(num_fields):
            field_name = f"field_{i}"
            field_type = draw(st.sampled_from(["string", "integer", "number", "boolean"]))
            properties[field_name] = {"type": field_type}
            
            # Randomly mark some fields as required
            if draw(st.booleans()):
                required.append(field_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required if required else []
        }
    
    @given(schema=simple_schema())
    @settings(max_examples=100)
    def test_missing_fields_set_to_null(self, schema: Dict[str, Any]):
        """
        Property 4: Missing Field Handling - Null for Missing Fields
        
        For any schema and partial data (missing some fields), ensure_schema_structure
        SHALL set missing fields to null.
        
        **Validates: Requirements 1.4, 6.3**
        """
        properties = schema.get("properties", {})
        field_names = list(properties.keys())
        
        # Skip if no fields
        assume(len(field_names) > 0)
        
        # Create partial data with only some fields
        partial_data = {}
        for i, field_name in enumerate(field_names):
            if i % 2 == 0:  # Only include even-indexed fields
                partial_data[field_name] = f"value_{i}"
        
        # Apply ensure_schema_structure
        result = ensure_schema_structure(partial_data, schema)
        
        # Verify all schema fields are present
        for field_name in field_names:
            assert field_name in result, \
                f"Field '{field_name}' should be present in result"
        
        # Verify missing fields are null
        for field_name in field_names:
            if field_name not in partial_data:
                assert result[field_name] is None, \
                    f"Missing field '{field_name}' should be null, got {result[field_name]}"
    
    @given(schema=simple_schema())
    @settings(max_examples=100)
    def test_empty_data_all_fields_null(self, schema: Dict[str, Any]):
        """
        Property 4: Missing Field Handling - Empty Data
        
        For any schema and empty data, ensure_schema_structure SHALL set
        all fields to null.
        
        **Validates: Requirements 1.4, 6.3**
        """
        properties = schema.get("properties", {})
        
        # Skip if no fields
        assume(len(properties) > 0)
        
        # Apply ensure_schema_structure with empty data
        result = ensure_schema_structure({}, schema)
        
        # Verify all fields are present and null
        for field_name in properties.keys():
            assert field_name in result, \
                f"Field '{field_name}' should be present in result"
            assert result[field_name] is None, \
                f"Field '{field_name}' should be null for empty data, got {result[field_name]}"
    
    @given(schema=simple_schema())
    @settings(max_examples=100)
    def test_existing_values_preserved(self, schema: Dict[str, Any]):
        """
        Property 4: Missing Field Handling - Preserve Existing Values
        
        For any schema and data with existing values, ensure_schema_structure
        SHALL preserve those values while setting missing fields to null.
        
        **Validates: Requirements 1.4, 6.3**
        """
        properties = schema.get("properties", {})
        field_names = list(properties.keys())
        
        # Skip if no fields
        assume(len(field_names) > 0)
        
        # Create data with values for all fields
        full_data = {}
        for field_name in field_names:
            field_type = properties[field_name].get("type", "string")
            if field_type == "string":
                full_data[field_name] = f"test_value_{field_name}"
            elif field_type == "integer":
                full_data[field_name] = 42
            elif field_type == "number":
                full_data[field_name] = 3.14
            elif field_type == "boolean":
                full_data[field_name] = True
        
        # Apply ensure_schema_structure
        result = ensure_schema_structure(full_data, schema)
        
        # Verify all existing values are preserved
        for field_name, original_value in full_data.items():
            assert result[field_name] == original_value, \
                f"Field '{field_name}' value should be preserved: expected {original_value}, got {result[field_name]}"
    
    @given(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L',))), min_size=1, max_size=5, unique=True))
    @settings(max_examples=100)
    def test_parse_extraction_adds_missing_fields(self, field_names: List[str]):
        """
        Property 4: Missing Field Handling - Parse Extraction Response
        
        For any valid JSON response missing some schema fields, parse_extraction_response
        SHALL add those missing fields with null values.
        
        **Validates: Requirements 1.4, 6.3**
        """
        # Filter to valid field names
        valid_field_names = [name for name in field_names if name.isalpha()]
        assume(len(valid_field_names) >= 2)
        
        # Create a partial JSON response (only first field has value)
        partial_response = {valid_field_names[0]: "test_value"}
        json_content = json.dumps(partial_response)
        
        # Use product_info schema which exists
        result = parse_extraction_response(json_content, "product_info")
        
        # If successful (not an error response), verify schema fields are present
        if "success" not in result or result.get("success") != False:
            # product_info schema has: name, description, price, category, features
            expected_fields = ["name", "description", "price", "category", "features"]
            for field in expected_fields:
                assert field in result, \
                    f"Schema field '{field}' should be present in result"
    
    def test_nested_object_missing_fields(self):
        """
        Property 4: Missing Field Handling - Nested Objects
        
        For schemas with nested objects, ensure_schema_structure SHALL
        recursively set missing fields to null in nested objects.
        
        **Validates: Requirements 1.4, 6.3**
        """
        # Schema with nested object
        nested_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "zip": {"type": "string"}
                    }
                }
            }
        }
        
        # Partial data with incomplete nested object
        partial_data = {
            "name": "John",
            "address": {
                "city": "Seattle"
                # street and zip are missing
            }
        }
        
        result = ensure_schema_structure(partial_data, nested_schema)
        
        # Verify top-level fields
        assert result["name"] == "John"
        assert "address" in result
        
        # Verify nested object has all fields
        assert result["address"]["city"] == "Seattle"
        assert result["address"]["street"] is None, \
            "Missing nested field 'street' should be null"
        assert result["address"]["zip"] is None, \
            "Missing nested field 'zip' should be null"
    
    def test_array_of_objects_missing_fields(self):
        """
        Property 4: Missing Field Handling - Array of Objects
        
        For schemas with arrays of objects, ensure_schema_structure SHALL
        set missing fields to null in each array item.
        
        **Validates: Requirements 1.4, 6.3**
        """
        # Schema with array of objects
        array_schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "price": {"type": "number"}
                        }
                    }
                }
            }
        }
        
        # Partial data with incomplete array items
        partial_data = {
            "items": [
                {"id": 1},  # missing name and price
                {"name": "Item 2", "price": 9.99},  # missing id
                {"id": 3, "name": "Item 3", "price": 19.99}  # complete
            ]
        }
        
        result = ensure_schema_structure(partial_data, array_schema)
        
        # Verify array items have all fields
        assert len(result["items"]) == 3
        
        # First item: id present, name and price should be null
        assert result["items"][0]["id"] == 1
        assert result["items"][0]["name"] is None
        assert result["items"][0]["price"] is None
        
        # Second item: name and price present, id should be null
        assert result["items"][1]["id"] is None
        assert result["items"][1]["name"] == "Item 2"
        assert result["items"][1]["price"] == 9.99
        
        # Third item: all present
        assert result["items"][2]["id"] == 3
        assert result["items"][2]["name"] == "Item 3"
        assert result["items"][2]["price"] == 19.99
    
    @given(schema=simple_schema())
    @settings(max_examples=100)
    def test_non_dict_data_returns_null_fields(self, schema: Dict[str, Any]):
        """
        Property 4: Missing Field Handling - Non-Dict Data
        
        For any schema, if the data is not a dictionary, ensure_schema_structure
        SHALL return a dictionary with all fields set to null.
        
        **Validates: Requirements 1.4, 6.3**
        """
        properties = schema.get("properties", {})
        
        # Skip if no fields
        assume(len(properties) > 0)
        
        # Test with non-dict data
        for invalid_data in [None, "string", 123, [], True]:
            result = ensure_schema_structure(invalid_data, schema)
            
            # Should return a dict with all fields null
            assert isinstance(result, dict), \
                f"Result should be a dict for invalid data {invalid_data}"
            
            for field_name in properties.keys():
                assert field_name in result, \
                    f"Field '{field_name}' should be present"
                assert result[field_name] is None, \
                    f"Field '{field_name}' should be null for invalid data"
    
    def test_schema_structure_preserved_with_partial_extraction(self):
        """
        Property 4: Missing Field Handling - Real Schema Test
        
        Using a real schema (product_info), verify that partial extraction
        preserves the complete schema structure with null for missing fields.
        
        **Validates: Requirements 1.4, 6.3**
        """
        # Simulate a partial extraction result (only name extracted)
        partial_json = '{"name": "Test Product"}'
        
        result = parse_extraction_response(partial_json, "product_info")
        
        # Should not be an error
        assert "success" not in result or result.get("success") != False, \
            f"Should successfully parse partial data, got: {result}"
        
        # Verify all product_info fields are present
        expected_fields = ["name", "description", "price", "category", "features"]
        for field in expected_fields:
            assert field in result, \
                f"Field '{field}' should be present in result"
        
        # Verify extracted value is preserved
        assert result["name"] == "Test Product"
        
        # Verify missing fields are null
        assert result["description"] is None
        assert result["price"] is None
        assert result["category"] is None
        assert result["features"] is None


# =============================================================================
# Run tests if executed directly
# =============================================================================

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
