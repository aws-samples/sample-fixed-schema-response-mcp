#!/usr/bin/env python3
"""
DynamoDB-backed StreamableHTTP Session Manager for MCP servers.

This module provides a custom StreamableHTTPSessionManager that uses DynamoDB
for session storage instead of in-memory storage, enabling horizontal scaling
across multiple Fargate tasks.

Feature: mcp-dynamodb-session
"""

import logging
from http import HTTPStatus
from typing import Any
from uuid import uuid4

import anyio
from anyio.abc import TaskStatus
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from mcp.server.lowlevel.server import Server as MCPServer
from mcp.server.streamable_http import (
    MCP_SESSION_ID_HEADER,
    EventStore,
    StreamableHTTPServerTransport,
)
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings

try:
    from .session_store import SessionStore
except ImportError:
    from session_store import SessionStore

logger = logging.getLogger(__name__)


class DynamoDBHTTPSessionManager(StreamableHTTPSessionManager):
    """
    StreamableHTTP Session Manager with DynamoDB-backed session storage.
    
    This extends the base StreamableHTTPSessionManager to use DynamoDB for
    session metadata storage, enabling horizontal scaling across multiple
    Fargate tasks. The actual transport instances are still in-memory per task,
    but session existence can be verified across tasks.
    
    Note: This is a partial solution. Full session state sharing would require
    serializing the entire transport state, which is complex. This implementation
    focuses on session ID validation and creation tracking.
    """
    
    def __init__(
        self,
        app: MCPServer[Any, Any],
        session_store: SessionStore | None = None,
        event_store: EventStore | None = None,
        json_response: bool = False,
        stateless: bool = False,
        security_settings: TransportSecuritySettings | None = None,
        retry_interval: int | None = None,
    ):
        super().__init__(
            app=app,
            event_store=event_store,
            json_response=json_response,
            stateless=stateless,
            security_settings=security_settings,
            retry_interval=retry_interval,
        )
        self._dynamo_store = session_store or SessionStore()
        logger.info("DynamoDBHTTPSessionManager initialized with DynamoDB session store")
    
    async def _handle_stateful_request(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """
        Handle stateful request with DynamoDB session tracking.
        
        This overrides the base implementation to:
        1. Check DynamoDB for session existence when not found locally
        2. Store new session IDs in DynamoDB
        3. Clean up DynamoDB on session termination
        """
        request = Request(scope, receive, send)
        request_mcp_session_id = request.headers.get(MCP_SESSION_ID_HEADER)
        
        logger.info(f"Handling stateful request, session_id from header: {request_mcp_session_id}")
        
        # Check if we have this session locally
        if request_mcp_session_id is not None and request_mcp_session_id in self._server_instances:
            transport = self._server_instances[request_mcp_session_id]
            logger.info(f"Found session {request_mcp_session_id} in local cache")
            await transport.handle_request(scope, receive, send)
            return
        
        # Session not found locally - check if it exists in DynamoDB
        if request_mcp_session_id is not None:
            dynamo_session = self._dynamo_store.load_session(request_mcp_session_id)
            if dynamo_session is not None:
                # Session exists in DynamoDB but not locally
                # This means the request hit a different task
                # We need to recreate the transport for this task
                logger.info(f"Session {request_mcp_session_id} found in DynamoDB, recreating transport")
                
                async with self._session_creation_lock:
                    # Double-check after acquiring lock
                    if request_mcp_session_id in self._server_instances:
                        transport = self._server_instances[request_mcp_session_id]
                        await transport.handle_request(scope, receive, send)
                        return
                    
                    # Create new transport with the existing session ID
                    http_transport = StreamableHTTPServerTransport(
                        mcp_session_id=request_mcp_session_id,
                        is_json_response_enabled=self.json_response,
                        event_store=self.event_store,
                        security_settings=self.security_settings,
                        retry_interval=self.retry_interval,
                    )
                    self._server_instances[request_mcp_session_id] = http_transport
                    
                    # Define the server runner (same pattern as base class)
                    async def run_server(*, task_status: TaskStatus[None] = anyio.TASK_STATUS_IGNORED) -> None:
                        async with http_transport.connect() as streams:
                            read_stream, write_stream = streams
                            task_status.started()
                            try:
                                await self.app.run(
                                    read_stream,
                                    write_stream,
                                    self.app.create_initialization_options(),
                                    stateless=False,
                                )
                            except Exception as e:
                                logger.error(f"Session {request_mcp_session_id} crashed: {e}", exc_info=True)
                            finally:
                                if (
                                    request_mcp_session_id in self._server_instances
                                    and not http_transport.is_terminated
                                ):
                                    logger.info(f"Cleaning up crashed session {request_mcp_session_id}")
                                    del self._server_instances[request_mcp_session_id]
                    
                    # Start the server task and wait for it to be ready
                    assert self._task_group is not None
                    await self._task_group.start(run_server)
                    logger.info(f"Recreated transport for session {request_mcp_session_id}")
                
                await http_transport.handle_request(scope, receive, send)
                return
            else:
                # Session ID provided but not found anywhere
                logger.warning(f"Session {request_mcp_session_id} not found in DynamoDB or local cache")
                response = Response(
                    content="Bad Request: No valid session ID provided",
                    status_code=HTTPStatus.BAD_REQUEST,
                    media_type="text/plain",
                )
                await response(scope, receive, send)
                return
        
        # No session ID provided - create new session
        async with self._session_creation_lock:
            new_session_id = uuid4().hex
            logger.info(f"Creating new session {new_session_id}")
            
            http_transport = StreamableHTTPServerTransport(
                mcp_session_id=new_session_id,
                is_json_response_enabled=self.json_response,
                event_store=self.event_store,
                security_settings=self.security_settings,
                retry_interval=self.retry_interval,
            )
            
            # Store session in DynamoDB
            try:
                self._dynamo_store.save_session(new_session_id, {
                    'initialized': True,
                    'task_id': 'unknown',
                })
                logger.info(f"Saved session {new_session_id} to DynamoDB")
            except Exception as e:
                logger.error(f"Failed to save session {new_session_id} to DynamoDB: {e}")
            
            self._server_instances[new_session_id] = http_transport
            
            # Define the server runner
            async def run_server(*, task_status: TaskStatus[None] = anyio.TASK_STATUS_IGNORED) -> None:
                async with http_transport.connect() as streams:
                    read_stream, write_stream = streams
                    task_status.started()
                    try:
                        await self.app.run(
                            read_stream,
                            write_stream,
                            self.app.create_initialization_options(),
                            stateless=False,
                        )
                    except Exception as e:
                        logger.error(f"Session {new_session_id} crashed: {e}", exc_info=True)
                    finally:
                        if (
                            new_session_id in self._server_instances
                            and not http_transport.is_terminated
                        ):
                            logger.info(f"Cleaning up crashed session {new_session_id}")
                            del self._server_instances[new_session_id]
                        # Clean up DynamoDB on session end
                        try:
                            self._dynamo_store.delete_session(new_session_id)
                            logger.info(f"Deleted session {new_session_id} from DynamoDB")
                        except Exception as e:
                            logger.error(f"Failed to delete session {new_session_id} from DynamoDB: {e}")
            
            # Start the server task and wait for it to be ready
            assert self._task_group is not None
            await self._task_group.start(run_server)
            logger.info(f"Created new transport with session ID: {new_session_id}")
        
        await http_transport.handle_request(scope, receive, send)
