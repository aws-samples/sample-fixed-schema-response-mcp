#!/usr/bin/env python3
"""
DynamoDB-backed session storage for MCP sessions.

This module provides a SessionStore class that handles all DynamoDB operations
for persisting and retrieving MCP session state. It enables horizontal scaling
across multiple Fargate tasks by externalizing session state.

Feature: mcp-dynamodb-session
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SessionStoreError(Exception):
    """Base exception for session store errors."""
    pass


class SessionNotFoundError(SessionStoreError):
    """Raised when a session is not found in DynamoDB."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session '{session_id}' not found in DynamoDB")


class SessionWriteError(SessionStoreError):
    """Raised when a DynamoDB write operation fails."""
    def __init__(self, session_id: str, operation: str, original_error: Exception):
        self.session_id = session_id
        self.operation = operation
        self.original_error = original_error
        super().__init__(
            f"Failed to {operation} session '{session_id}': {str(original_error)}"
        )


class SessionReadError(SessionStoreError):
    """Raised when a DynamoDB read operation fails."""
    def __init__(self, session_id: str, original_error: Exception):
        self.session_id = session_id
        self.original_error = original_error
        super().__init__(
            f"Failed to read session '{session_id}': {str(original_error)}"
        )


class SessionStore:
    """DynamoDB-backed session storage for MCP sessions.
    
    This class encapsulates all DynamoDB operations for session persistence,
    including save, load, update, and delete operations with TTL support.
    
    Environment Variables:
        SESSION_TABLE_NAME: DynamoDB table name (default: 'mcp-sessions')
        SESSION_TTL_HOURS: Session TTL in hours (default: 24)
    """
    
    def __init__(self, dynamodb_resource=None, table_name: Optional[str] = None, ttl_hours: Optional[int] = None):
        """Initialize the session store with environment variable configuration.
        
        Args:
            dynamodb_resource: Optional boto3 DynamoDB resource (for testing with DynamoDB Local)
            table_name: Optional table name override (defaults to SESSION_TABLE_NAME env var)
            ttl_hours: Optional TTL hours override (defaults to SESSION_TTL_HOURS env var)
        """
        self.table_name = table_name or os.getenv('SESSION_TABLE_NAME', 'mcp-sessions')
        self.ttl_hours = ttl_hours or int(os.getenv('SESSION_TTL_HOURS', '24'))
        self.dynamodb = dynamodb_resource or boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"SessionStore initialized with table={self.table_name}, ttl_hours={self.ttl_hours}")
    
    def save_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """Save session state to DynamoDB with TTL.
        
        Args:
            session_id: Unique session identifier
            state: Session state dictionary to persist
            
        Raises:
            SessionWriteError: If DynamoDB write operation fails
        """
        ttl = int((datetime.now() + timedelta(hours=self.ttl_hours)).timestamp())
        try:
            self.table.put_item(Item={
                'session_id': session_id,
                'state': json.dumps(state),
                'created_at': datetime.now().isoformat(),
                'ttl': ttl
            })
            logger.info(f"Saved session {session_id}")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"DynamoDB error saving session {session_id}: {e}")
            raise SessionWriteError(session_id, "save", e)
        except Exception as e:
            logger.error(f"Unexpected error saving session {session_id}: {e}")
            raise SessionWriteError(session_id, "save", e)
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session state from DynamoDB.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Deserialized session state dictionary, or None if not found
            
        Note:
            Returns None on read errors (per requirement 6.2) to allow graceful degradation.
            Errors are logged with full context for debugging.
        """
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            if 'Item' in response:
                logger.info(f"Loaded session {session_id}")
                return json.loads(response['Item']['state'])
            logger.info(f"Session {session_id} not found")
            return None
        except (ClientError, BotoCoreError) as e:
            # Log DynamoDB-specific errors with context (requirement 6.3)
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"DynamoDB error loading session {session_id}: "
                f"ErrorCode={error_code}, Details={e}"
            )
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize session {session_id} state: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> None:
        """Delete session from DynamoDB.
        
        Args:
            session_id: Unique session identifier
            
        Raises:
            SessionWriteError: If DynamoDB delete operation fails
        """
        try:
            self.table.delete_item(Key={'session_id': session_id})
            logger.info(f"Deleted session {session_id}")
        except (ClientError, BotoCoreError) as e:
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"DynamoDB error deleting session {session_id}: "
                f"ErrorCode={error_code}, Details={e}"
            )
            raise SessionWriteError(session_id, "delete", e)
        except Exception as e:
            logger.error(f"Unexpected error deleting session {session_id}: {e}")
            raise SessionWriteError(session_id, "delete", e)
    
    def update_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """Update existing session state and refresh TTL.
        
        Args:
            session_id: Unique session identifier
            state: Updated session state dictionary
            
        Raises:
            SessionWriteError: If DynamoDB update operation fails
        """
        ttl = int((datetime.now() + timedelta(hours=self.ttl_hours)).timestamp())
        try:
            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET #state = :state, #ttl = :ttl, updated_at = :updated',
                ExpressionAttributeNames={
                    '#state': 'state',
                    '#ttl': 'ttl'
                },
                ExpressionAttributeValues={
                    ':state': json.dumps(state),
                    ':ttl': ttl,
                    ':updated': datetime.now().isoformat()
                }
            )
            logger.info(f"Updated session {session_id}")
        except (ClientError, BotoCoreError) as e:
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"DynamoDB error updating session {session_id}: "
                f"ErrorCode={error_code}, Details={e}"
            )
            raise SessionWriteError(session_id, "update", e)
        except Exception as e:
            logger.error(f"Unexpected error updating session {session_id}: {e}")
            raise SessionWriteError(session_id, "update", e)
