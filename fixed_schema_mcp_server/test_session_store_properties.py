#!/usr/bin/env python3
"""
Property-based tests for the MCP DynamoDB Session Management feature.

These tests validate the correctness properties defined in the design document
using the hypothesis library for property-based testing.

Feature: mcp-dynamodb-session

Note: These tests require DynamoDB Local running on localhost:8000.
Start it with: docker compose up -d dynamodb-local
"""

import json
import os
import uuid
import time
from datetime import datetime, timedelta
from typing import Any, Dict
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import pytest
import boto3
from botocore.config import Config

# Set environment variables for testing before importing session_store
os.environ['SESSION_TABLE_NAME'] = 'test-mcp-sessions'
os.environ['SESSION_TTL_HOURS'] = '24'


# =============================================================================
# Test Fixtures and Setup
# =============================================================================

@pytest.fixture(scope="module")
def dynamodb_local():
    """Create a DynamoDB Local client and test table."""
    # Configure boto3 to use DynamoDB Local
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='testing',
        aws_secret_access_key='testing'
    )
    
    table_name = 'test-mcp-sessions'
    
    # Delete table if it exists
    try:
        table = dynamodb.Table(table_name)
        table.delete()
        table.wait_until_not_exists()
    except Exception:
        pass
    
    # Create the test table
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'session_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'session_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()
    
    yield dynamodb
    
    # Cleanup
    try:
        table.delete()
    except Exception:
        pass


@pytest.fixture
def session_store(dynamodb_local):
    """Create a SessionStore instance configured for DynamoDB Local."""
    from fixed_schema_mcp_server.session_store import SessionStore
    return SessionStore(
        dynamodb_resource=dynamodb_local,
        table_name='test-mcp-sessions',
        ttl_hours=24
    )


# =============================================================================
# Test Strategies (Generators)
# =============================================================================

# Strategy for generating valid session IDs (UUIDs)
session_ids = st.uuids().map(str)

# Strategy for generating simple session state values
simple_values = st.one_of(
    st.text(min_size=0, max_size=100),
    st.integers(min_value=-10000, max_value=10000),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
)

# Strategy for generating session state dictionaries
@st.composite
def session_state(draw):
    """Generate a valid session state dictionary."""
    # Generate a dictionary with string keys and JSON-serializable values
    num_fields = draw(st.integers(min_value=1, max_value=10))
    state = {}
    
    for i in range(num_fields):
        key = f"field_{i}"
        value_type = draw(st.sampled_from(['string', 'int', 'float', 'bool', 'list', 'dict', 'none']))
        
        if value_type == 'string':
            state[key] = draw(st.text(min_size=0, max_size=50))
        elif value_type == 'int':
            state[key] = draw(st.integers(min_value=-10000, max_value=10000))
        elif value_type == 'float':
            state[key] = draw(st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
        elif value_type == 'bool':
            state[key] = draw(st.booleans())
        elif value_type == 'list':
            state[key] = draw(st.lists(st.text(min_size=0, max_size=20), max_size=5))
        elif value_type == 'dict':
            state[key] = draw(st.dictionaries(
                st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L',))),
                st.text(min_size=0, max_size=20),
                max_size=3
            ))
        else:
            state[key] = None
    
    return state


# Strategy for MCP-like session state
@st.composite
def mcp_session_state(draw):
    """Generate a session state that resembles MCP session data."""
    return {
        'initialized': draw(st.booleans()),
        'capabilities': {
            'tools': draw(st.booleans()),
            'resources': draw(st.booleans()),
            'prompts': draw(st.booleans()),
        },
        'subscriptions': draw(st.lists(st.text(min_size=1, max_size=20), max_size=5)),
        'client_info': {
            'name': draw(st.text(min_size=1, max_size=30)),
            'version': draw(st.from_regex(r'[0-9]+\.[0-9]+\.[0-9]+', fullmatch=True)),
        }
    }


# =============================================================================
# Property 3: Session Store Round-Trip
# Validates: Requirements 3.1, 3.2, 3.5, 3.6
#
# *For any* valid session state dictionary, saving the session with `save_session`
# and then loading it with `load_session` SHALL return an equivalent state dictionary.
# =============================================================================

class TestSessionStoreRoundTrip:
    """
    Feature: mcp-dynamodb-session, Property 3: Session Store Round-Trip
    Validates: Requirements 3.1, 3.2, 3.5, 3.6
    """
    
    @given(state=session_state())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_then_load_returns_equivalent_state(self, session_store, state: Dict[str, Any]):
        """
        Property 3: Session Store Round-Trip
        
        For any valid session state dictionary, saving the session with save_session
        and then loading it with load_session SHALL return an equivalent state dictionary.
        
        **Validates: Requirements 3.1, 3.2, 3.5, 3.6**
        """
        session_id = str(uuid.uuid4())
        
        # Save the session
        session_store.save_session(session_id, state)
        
        # Load the session
        loaded_state = session_store.load_session(session_id)
        
        # Verify round-trip equivalence
        assert loaded_state is not None, "Loaded state should not be None"
        assert loaded_state == state, f"Loaded state should equal saved state. Expected: {state}, Got: {loaded_state}"
        
        # Cleanup
        session_store.delete_session(session_id)
    
    @given(state=mcp_session_state())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mcp_session_state_round_trip(self, session_store, state: Dict[str, Any]):
        """
        Property 3: Session Store Round-Trip - MCP Session State
        
        For any MCP-like session state, the round-trip SHALL preserve all fields.
        
        **Validates: Requirements 3.1, 3.2, 3.5, 3.6**
        """
        session_id = str(uuid.uuid4())
        
        # Save the session
        session_store.save_session(session_id, state)
        
        # Load the session
        loaded_state = session_store.load_session(session_id)
        
        # Verify all MCP fields are preserved
        assert loaded_state is not None, "Loaded state should not be None"
        assert loaded_state['initialized'] == state['initialized']
        assert loaded_state['capabilities'] == state['capabilities']
        assert loaded_state['subscriptions'] == state['subscriptions']
        assert loaded_state['client_info'] == state['client_info']
        
        # Cleanup
        session_store.delete_session(session_id)



# =============================================================================
# Property 4: Session Store Delete Removes Session
# Validates: Requirements 3.4
#
# *For any* saved session, calling `delete_session` and then `load_session`
# SHALL return None.
# =============================================================================

class TestSessionStoreDelete:
    """
    Feature: mcp-dynamodb-session, Property 4: Session Store Delete Removes Session
    Validates: Requirements 3.4
    """
    
    @given(state=session_state())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_delete_then_load_returns_none(self, session_store, state: Dict[str, Any]):
        """
        Property 4: Session Store Delete Removes Session
        
        For any saved session, calling delete_session and then load_session
        SHALL return None.
        
        **Validates: Requirements 3.4**
        """
        session_id = str(uuid.uuid4())
        
        # Save the session
        session_store.save_session(session_id, state)
        
        # Verify it exists
        loaded = session_store.load_session(session_id)
        assert loaded is not None, "Session should exist after save"
        
        # Delete the session
        session_store.delete_session(session_id)
        
        # Verify it's gone
        loaded_after_delete = session_store.load_session(session_id)
        assert loaded_after_delete is None, "Session should be None after delete"


# =============================================================================
# Property 5: Session Store TTL Within Expected Range
# Validates: Requirements 3.7
#
# *For any* saved session, the TTL value stored in DynamoDB SHALL be within
# the expected range (current time + configured TTL hours ± 1 minute tolerance).
# =============================================================================

class TestSessionStoreTTL:
    """
    Feature: mcp-dynamodb-session, Property 5: Session Store TTL Within Expected Range
    Validates: Requirements 3.7
    """
    
    @given(state=session_state())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_ttl_within_expected_range(self, session_store, dynamodb_local, state: Dict[str, Any]):
        """
        Property 5: Session Store TTL Within Expected Range
        
        For any saved session, the TTL value stored in DynamoDB SHALL be within
        the expected range (current time + configured TTL hours ± 1 minute tolerance).
        
        **Validates: Requirements 3.7**
        """
        session_id = str(uuid.uuid4())
        
        # Record time before save
        before_save = datetime.now()
        
        # Save the session
        session_store.save_session(session_id, state)
        
        # Record time after save
        after_save = datetime.now()
        
        # Get the raw item from DynamoDB to check TTL
        table = dynamodb_local.Table('test-mcp-sessions')
        response = table.get_item(Key={'session_id': session_id})
        
        assert 'Item' in response, "Item should exist in DynamoDB"
        stored_ttl = response['Item']['ttl']
        
        # Calculate expected TTL range (24 hours ± 1 minute tolerance)
        ttl_hours = int(os.getenv('SESSION_TTL_HOURS', '24'))
        expected_min = int((before_save + timedelta(hours=ttl_hours) - timedelta(minutes=1)).timestamp())
        expected_max = int((after_save + timedelta(hours=ttl_hours) + timedelta(minutes=1)).timestamp())
        
        assert expected_min <= stored_ttl <= expected_max, \
            f"TTL {stored_ttl} should be between {expected_min} and {expected_max}"
        
        # Cleanup
        session_store.delete_session(session_id)
    
    @given(state=session_state())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_update_refreshes_ttl(self, session_store, dynamodb_local, state: Dict[str, Any]):
        """
        Property 5: Session Store TTL - Update Refreshes TTL
        
        For any session update, the TTL SHALL be refreshed to current time + TTL hours.
        
        **Validates: Requirements 3.7**
        """
        session_id = str(uuid.uuid4())
        
        # Save initial session
        session_store.save_session(session_id, state)
        
        # Get initial TTL
        table = dynamodb_local.Table('test-mcp-sessions')
        initial_response = table.get_item(Key={'session_id': session_id})
        initial_ttl = initial_response['Item']['ttl']
        
        # Small delay to ensure time difference
        time.sleep(0.1)
        
        # Update the session
        updated_state = {**state, 'updated': True}
        before_update = datetime.now()
        session_store.update_session(session_id, updated_state)
        after_update = datetime.now()
        
        # Get updated TTL
        updated_response = table.get_item(Key={'session_id': session_id})
        updated_ttl = updated_response['Item']['ttl']
        
        # TTL should be refreshed (>= initial or within expected range)
        ttl_hours = int(os.getenv('SESSION_TTL_HOURS', '24'))
        expected_min = int((before_update + timedelta(hours=ttl_hours) - timedelta(minutes=1)).timestamp())
        expected_max = int((after_update + timedelta(hours=ttl_hours) + timedelta(minutes=1)).timestamp())
        
        assert expected_min <= updated_ttl <= expected_max, \
            f"Updated TTL {updated_ttl} should be between {expected_min} and {expected_max}"
        
        # Cleanup
        session_store.delete_session(session_id)


# =============================================================================
# Property 6: Load Non-Existent Session Returns None
# Validates: Requirements 3.3
#
# *For any* randomly generated session_id that was never saved, `load_session`
# SHALL return None.
# =============================================================================

class TestLoadNonExistentSession:
    """
    Feature: mcp-dynamodb-session, Property 6: Load Non-Existent Session Returns None
    Validates: Requirements 3.3
    """
    
    @given(session_id=session_ids)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_load_nonexistent_returns_none(self, session_store, session_id: str):
        """
        Property 6: Load Non-Existent Session Returns None
        
        For any randomly generated session_id that was never saved, load_session
        SHALL return None.
        
        **Validates: Requirements 3.3**
        """
        # Ensure this session doesn't exist by using a fresh UUID
        fresh_session_id = str(uuid.uuid4())
        
        # Load should return None
        result = session_store.load_session(fresh_session_id)
        
        assert result is None, f"Loading non-existent session should return None, got {result}"
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_load_arbitrary_id_returns_none(self, session_store, arbitrary_id: str):
        """
        Property 6: Load Non-Existent Session - Arbitrary IDs
        
        For any arbitrary string used as session_id that was never saved,
        load_session SHALL return None.
        
        **Validates: Requirements 3.3**
        """
        # Make the ID unique by appending a UUID
        unique_id = f"{arbitrary_id}_{uuid.uuid4()}"
        
        # Load should return None
        result = session_store.load_session(unique_id)
        
        assert result is None, f"Loading non-existent session should return None, got {result}"


# =============================================================================
# Property 7: Session Manager Creates Unique Sessions
# Validates: Requirements 4.1
#
# *For any* number of session creations, all generated session IDs SHALL be
# unique and all sessions SHALL be retrievable from DynamoDB.
# =============================================================================

class TestSessionManagerUniqueSessions:
    """
    Feature: mcp-dynamodb-session, Property 7: Session Manager Creates Unique Sessions
    Validates: Requirements 4.1
    """
    
    @pytest.fixture
    def session_manager(self, dynamodb_local):
        """Create a DynamoDBSessionManager instance configured for DynamoDB Local."""
        from fixed_schema_mcp_server.session_store import SessionStore
        from fixed_schema_mcp_server.session_manager import DynamoDBSessionManager
        
        store = SessionStore(
            dynamodb_resource=dynamodb_local,
            table_name='test-mcp-sessions',
            ttl_hours=24
        )
        return DynamoDBSessionManager(session_store=store)
    
    @given(num_sessions=st.integers(min_value=1, max_value=20))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_all_created_sessions_are_unique(self, session_manager, num_sessions: int):
        """
        Property 7: Session Manager Creates Unique Sessions
        
        For any number of session creations, all generated session IDs SHALL be
        unique and all sessions SHALL be retrievable from DynamoDB.
        
        **Validates: Requirements 4.1**
        """
        created_session_ids = []
        
        # Create multiple sessions
        for _ in range(num_sessions):
            session_id = session_manager.create_session()
            created_session_ids.append(session_id)
        
        # Verify all session IDs are unique
        assert len(created_session_ids) == len(set(created_session_ids)), \
            f"All session IDs should be unique. Got duplicates in: {created_session_ids}"
        
        # Verify all sessions are retrievable
        for session_id in created_session_ids:
            session = session_manager.get_session(session_id)
            assert session is not None, f"Session {session_id} should be retrievable"
            assert 'initialized' in session, "Session should have 'initialized' field"
            assert 'capabilities' in session, "Session should have 'capabilities' field"
            assert 'subscriptions' in session, "Session should have 'subscriptions' field"
        
        # Cleanup
        for session_id in created_session_ids:
            session_manager.delete_session(session_id)
    
    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_session_ids_are_valid_uuids(self, session_manager, data):
        """
        Property 7: Session Manager Creates Unique Sessions - UUID Format
        
        For any created session, the session ID SHALL be a valid UUID string.
        
        **Validates: Requirements 4.1**
        """
        session_id = session_manager.create_session()
        
        # Verify it's a valid UUID
        try:
            parsed_uuid = uuid.UUID(session_id)
            assert str(parsed_uuid) == session_id, "Session ID should be a valid UUID string"
        except ValueError:
            pytest.fail(f"Session ID '{session_id}' is not a valid UUID")
        
        # Cleanup
        session_manager.delete_session(session_id)
    
    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_created_session_has_initial_state(self, session_manager, data):
        """
        Property 7: Session Manager Creates Unique Sessions - Initial State
        
        For any created session, the initial state SHALL contain the expected
        default fields (initialized=False, empty capabilities, empty subscriptions).
        
        **Validates: Requirements 4.1**
        """
        session_id = session_manager.create_session()
        
        # Retrieve the session
        session = session_manager.get_session(session_id)
        
        # Verify initial state structure
        assert session is not None, "Created session should be retrievable"
        assert session['initialized'] == False, "Initial state should have initialized=False"
        assert session['capabilities'] == {}, "Initial state should have empty capabilities"
        assert session['subscriptions'] == [], "Initial state should have empty subscriptions"
        
        # Cleanup
        session_manager.delete_session(session_id)
