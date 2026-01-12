#!/usr/bin/env python3
"""
DynamoDB Session Manager for MCP sessions.

This module provides a DynamoDBSessionManager class that wraps FastMCP's session
handling to use external DynamoDB storage, enabling horizontal scaling across
multiple Fargate tasks.

Feature: mcp-dynamodb-session
"""

import uuid
import logging
from typing import Optional, Dict, Any

try:
    from .session_store import SessionStore, SessionStoreError, SessionWriteError, SessionNotFoundError
except ImportError:
    from session_store import SessionStore, SessionStoreError, SessionWriteError, SessionNotFoundError

logger = logging.getLogger(__name__)


class DynamoDBSessionManager:
    """Custom session manager using DynamoDB for persistence.
    
    This class provides a high-level interface for managing MCP sessions
    with DynamoDB as the backing store. It handles session creation with
    UUID generation, retrieval, updates, and deletion.
    
    Attributes:
        store: The underlying SessionStore instance for DynamoDB operations
    """
    
    def __init__(self, session_store: Optional[SessionStore] = None):
        """Initialize the session manager.
        
        Args:
            session_store: Optional SessionStore instance (for testing).
                          If not provided, creates a new SessionStore.
        """
        self.store = session_store or SessionStore()
        logger.info("DynamoDBSessionManager initialized")
    
    def create_session(self) -> str:
        """Create a new session and store initial state.
        
        Generates a unique session ID using UUID4 and stores the initial
        session state in DynamoDB.
        
        Returns:
            The generated unique session ID (UUID string)
            
        Raises:
            SessionWriteError: If DynamoDB write operation fails
        """
        session_id = str(uuid.uuid4())
        initial_state = {
            'initialized': False,
            'capabilities': {},
            'subscriptions': [],
        }
        try:
            self.store.save_session(session_id, initial_state)
            logger.info(f"Created new session {session_id}")
            return session_id
        except SessionWriteError as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating session {session_id}: {e}")
            raise SessionWriteError(session_id, "create", e)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session state from DynamoDB.
        
        Args:
            session_id: The unique session identifier
            
        Returns:
            The session state dictionary, or None if not found
        """
        state = self.store.load_session(session_id)
        if state is None:
            logger.warning(f"Session {session_id} not found")
        return state
    
    def update_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """Update session state in DynamoDB.
        
        Args:
            session_id: The unique session identifier
            state: The updated session state dictionary
            
        Raises:
            SessionWriteError: If DynamoDB update operation fails
        """
        try:
            self.store.update_session(session_id, state)
            logger.info(f"Updated session {session_id}")
        except SessionWriteError as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating session {session_id}: {e}")
            raise SessionWriteError(session_id, "update", e)
    
    def delete_session(self, session_id: str) -> None:
        """Delete session from DynamoDB.
        
        Args:
            session_id: The unique session identifier
            
        Raises:
            SessionWriteError: If DynamoDB delete operation fails
        """
        try:
            self.store.delete_session(session_id)
            logger.info(f"Deleted session {session_id}")
        except SessionWriteError as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting session {session_id}: {e}")
            raise SessionWriteError(session_id, "delete", e)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists in DynamoDB.
        
        Args:
            session_id: The unique session identifier
            
        Returns:
            True if the session exists, False otherwise
        """
        return self.store.load_session(session_id) is not None
