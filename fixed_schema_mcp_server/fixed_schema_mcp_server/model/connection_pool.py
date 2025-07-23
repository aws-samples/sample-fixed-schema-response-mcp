"""
Connection pooling functionality for the Fixed Schema Response MCP Server.

This module provides functionality for managing connections to model APIs,
implementing connection pooling, health checks, and connection management.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable, TypeVar, Generic, Union
import random
from dataclasses import dataclass
from enum import Enum

from fixed_schema_mcp_server.model.exceptions import (
    ModelConnectionError,
    ModelTimeoutError
)

logger = logging.getLogger(__name__)

# Type variable for the connection type
T = TypeVar('T')


class ConnectionStatus(Enum):
    """Status of a connection in the pool."""
    IDLE = "idle"
    BUSY = "busy"
    UNHEALTHY = "unhealthy"
    CLOSED = "closed"


@dataclass
class PooledConnection(Generic[T]):
    """
    A connection in the connection pool.
    
    Attributes:
        connection: The actual connection object
        status: The status of the connection
        created_at: The time when the connection was created
        last_used_at: The time when the connection was last used
        error_count: The number of errors that occurred on this connection
        health_check_at: The time when the connection was last health checked
    """
    connection: T
    status: ConnectionStatus = ConnectionStatus.IDLE
    created_at: float = 0.0
    last_used_at: float = 0.0
    error_count: int = 0
    health_check_at: float = 0.0


class ConnectionPool(Generic[T]):
    """
    A connection pool for managing connections to external services.
    
    This class implements a connection pool that manages connections to external
    services, such as model APIs. It provides functionality for creating, acquiring,
    releasing, and health checking connections.
    """
    
    def __init__(
        self,
        create_connection: Callable[[], Awaitable[T]],
        health_check: Callable[[T], Awaitable[bool]],
        close_connection: Callable[[T], Awaitable[None]],
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: float = 300.0,  # 5 minutes
        health_check_interval: float = 60.0,  # 1 minute
        max_errors: int = 3
    ):
        """
        Initialize the connection pool.
        
        Args:
            create_connection: A function that creates a new connection
            health_check: A function that checks if a connection is healthy
            close_connection: A function that closes a connection
            min_size: The minimum number of connections to maintain
            max_size: The maximum number of connections to allow
            max_idle_time: The maximum time a connection can be idle before being closed
            health_check_interval: The interval between health checks
            max_errors: The maximum number of errors before a connection is considered unhealthy
        """
        self._create_connection = create_connection
        self._health_check = health_check
        self._close_connection = close_connection
        self._min_size = min_size
        self._max_size = max_size
        self._max_idle_time = max_idle_time
        self._health_check_interval = health_check_interval
        self._max_errors = max_errors
        
        self._connections: List[PooledConnection[T]] = []
        self._lock = asyncio.Lock()
        self._maintenance_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """
        Start the connection pool.
        
        This method initializes the minimum number of connections and starts
        the maintenance task.
        """
        if self._running:
            return
        
        self._running = True
        
        # Initialize the minimum number of connections
        async with self._lock:
            for _ in range(self._min_size):
                try:
                    connection = await self._create_connection()
                    self._connections.append(PooledConnection(
                        connection=connection,
                        status=ConnectionStatus.IDLE,
                        created_at=time.time(),
                        last_used_at=time.time(),
                        health_check_at=time.time()
                    ))
                except Exception as e:
                    logger.error(f"Error creating initial connection: {e}")
        
        # Start the maintenance task
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        
        logger.info(f"Connection pool started with {len(self._connections)} connections")
    
    async def stop(self) -> None:
        """
        Stop the connection pool.
        
        This method stops the maintenance task and closes all connections.
        """
        if not self._running:
            return
        
        self._running = False
        
        # Cancel the maintenance task
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
            self._maintenance_task = None
        
        # Close all connections
        async with self._lock:
            for pooled_conn in self._connections:
                try:
                    await self._close_connection(pooled_conn.connection)
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            self._connections.clear()
        
        logger.info("Connection pool stopped")
    
    async def acquire(self, timeout: float = 10.0) -> T:
        """
        Acquire a connection from the pool.
        
        Args:
            timeout: The maximum time to wait for a connection
            
        Returns:
            A connection from the pool
            
        Raises:
            ModelConnectionError: If no connection could be acquired
            ModelTimeoutError: If the timeout was reached
        """
        start_time = time.time()
        
        while True:
            # Check if we've exceeded the timeout
            if time.time() - start_time > timeout:
                raise ModelTimeoutError(
                    "Timeout waiting for connection from pool",
                    timeout=timeout
                )
            
            # Try to get an idle connection
            async with self._lock:
                # First, try to find an idle connection
                for pooled_conn in self._connections:
                    if pooled_conn.status == ConnectionStatus.IDLE:
                        pooled_conn.status = ConnectionStatus.BUSY
                        pooled_conn.last_used_at = time.time()
                        return pooled_conn.connection
                
                # If no idle connection is available, try to create a new one
                if len(self._connections) < self._max_size:
                    try:
                        connection = await self._create_connection()
                        pooled_conn = PooledConnection(
                            connection=connection,
                            status=ConnectionStatus.BUSY,
                            created_at=time.time(),
                            last_used_at=time.time(),
                            health_check_at=time.time()
                        )
                        self._connections.append(pooled_conn)
                        return connection
                    except Exception as e:
                        logger.error(f"Error creating new connection: {e}")
                        raise ModelConnectionError(
                            f"Failed to create new connection: {str(e)}",
                            cause=e
                        )
            
            # If we get here, all connections are busy and we're at max size
            # Wait a bit and try again
            await asyncio.sleep(0.1)
    
    async def release(self, connection: T) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: The connection to release
        """
        async with self._lock:
            # Find the connection in the pool
            for pooled_conn in self._connections:
                if pooled_conn.connection == connection:
                    pooled_conn.status = ConnectionStatus.IDLE
                    pooled_conn.last_used_at = time.time()
                    return
            
            # If we get here, the connection wasn't found in the pool
            logger.warning("Attempted to release a connection that isn't in the pool")
    
    async def mark_unhealthy(self, connection: T) -> None:
        """
        Mark a connection as unhealthy.
        
        Args:
            connection: The connection to mark as unhealthy
        """
        async with self._lock:
            # Find the connection in the pool
            for pooled_conn in self._connections:
                if pooled_conn.connection == connection:
                    pooled_conn.status = ConnectionStatus.UNHEALTHY
                    pooled_conn.error_count += 1
                    return
    
    async def _maintenance_loop(self) -> None:
        """
        Maintenance loop for the connection pool.
        
        This method runs periodically to:
        - Close idle connections that have exceeded the max idle time
        - Close unhealthy connections
        - Ensure the minimum number of connections is maintained
        - Perform health checks on connections
        """
        while self._running:
            try:
                await self._perform_maintenance()
            except Exception as e:
                logger.error(f"Error in connection pool maintenance: {e}")
            
            # Wait before the next maintenance cycle
            await asyncio.sleep(self._health_check_interval)
    
    async def _perform_maintenance(self) -> None:
        """Perform maintenance on the connection pool."""
        now = time.time()
        connections_to_close = []
        
        async with self._lock:
            # Identify connections to close
            for pooled_conn in self._connections:
                # Close connections that have been idle for too long
                if (pooled_conn.status == ConnectionStatus.IDLE and
                        now - pooled_conn.last_used_at > self._max_idle_time and
                        len(self._connections) > self._min_size):
                    connections_to_close.append(pooled_conn)
                    continue
                
                # Close unhealthy connections
                if pooled_conn.status == ConnectionStatus.UNHEALTHY:
                    connections_to_close.append(pooled_conn)
                    continue
                
                # Perform health checks on idle connections
                if (pooled_conn.status == ConnectionStatus.IDLE and
                        now - pooled_conn.health_check_at > self._health_check_interval):
                    try:
                        is_healthy = await self._health_check(pooled_conn.connection)
                        pooled_conn.health_check_at = now
                        if not is_healthy:
                            pooled_conn.status = ConnectionStatus.UNHEALTHY
                            connections_to_close.append(pooled_conn)
                    except Exception as e:
                        logger.error(f"Error during connection health check: {e}")
                        pooled_conn.error_count += 1
                        if pooled_conn.error_count >= self._max_errors:
                            pooled_conn.status = ConnectionStatus.UNHEALTHY
                            connections_to_close.append(pooled_conn)
            
            # Close connections
            for pooled_conn in connections_to_close:
                try:
                    await self._close_connection(pooled_conn.connection)
                    self._connections.remove(pooled_conn)
                    logger.debug(f"Closed connection (status: {pooled_conn.status.value})")
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            
            # Ensure minimum connections
            connections_to_create = max(0, self._min_size - len(self._connections))
            for _ in range(connections_to_create):
                try:
                    connection = await self._create_connection()
                    self._connections.append(PooledConnection(
                        connection=connection,
                        status=ConnectionStatus.IDLE,
                        created_at=now,
                        last_used_at=now,
                        health_check_at=now
                    ))
                    logger.debug("Created new connection to maintain minimum pool size")
                except Exception as e:
                    logger.error(f"Error creating connection during maintenance: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the connection pool.
        
        Returns:
            A dictionary containing statistics about the connection pool
        """
        stats = {
            "total_connections": len(self._connections),
            "idle_connections": 0,
            "busy_connections": 0,
            "unhealthy_connections": 0,
            "min_size": self._min_size,
            "max_size": self._max_size,
            "max_idle_time": self._max_idle_time,
            "health_check_interval": self._health_check_interval
        }
        
        for pooled_conn in self._connections:
            if pooled_conn.status == ConnectionStatus.IDLE:
                stats["idle_connections"] += 1
            elif pooled_conn.status == ConnectionStatus.BUSY:
                stats["busy_connections"] += 1
            elif pooled_conn.status == ConnectionStatus.UNHEALTHY:
                stats["unhealthy_connections"] += 1
        
        return stats