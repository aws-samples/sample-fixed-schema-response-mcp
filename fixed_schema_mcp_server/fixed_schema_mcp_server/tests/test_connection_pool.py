"""
Tests for the connection pool module.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from fixed_schema_mcp_server.model.connection_pool import ConnectionPool, ConnectionStatus, PooledConnection
from fixed_schema_mcp_server.model.exceptions import ModelConnectionError, ModelTimeoutError


class TestConnectionPool:
    """Test cases for the ConnectionPool class."""
    
    @pytest.fixture
    async def mock_connection_pool(self):
        """Create a mock connection pool for testing."""
        # Create mock functions
        create_connection = AsyncMock()
        health_check = AsyncMock(return_value=True)
        close_connection = AsyncMock()
        
        # Create a test connection
        test_connection = MagicMock()
        create_connection.return_value = test_connection
        
        # Create the connection pool
        pool = ConnectionPool(
            create_connection=create_connection,
            health_check=health_check,
            close_connection=close_connection,
            min_size=1,
            max_size=3,
            max_idle_time=1.0,  # Short for testing
            health_check_interval=0.5  # Short for testing
        )
        
        # Start the pool
        await pool.start()
        
        # Return the pool and mocks
        yield pool, create_connection, health_check, close_connection, test_connection
        
        # Stop the pool
        await pool.stop()
    
    @pytest.mark.asyncio
    async def test_start_creates_min_connections(self, mock_connection_pool):
        """Test that starting the pool creates the minimum number of connections."""
        pool, create_connection, _, _, _ = mock_connection_pool
        
        # Check that the minimum number of connections were created
        stats = pool.get_stats()
        assert stats["total_connections"] == 1
        assert stats["idle_connections"] == 1
        
        # Check that create_connection was called once
        create_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_acquire_release(self, mock_connection_pool):
        """Test acquiring and releasing a connection."""
        pool, _, _, _, test_connection = mock_connection_pool
        
        # Acquire a connection
        conn = await pool.acquire()
        assert conn == test_connection
        
        # Check stats after acquire
        stats = pool.get_stats()
        assert stats["busy_connections"] == 1
        assert stats["idle_connections"] == 0
        
        # Release the connection
        await pool.release(conn)
        
        # Check stats after release
        stats = pool.get_stats()
        assert stats["busy_connections"] == 0
        assert stats["idle_connections"] == 1
    
    @pytest.mark.asyncio
    async def test_acquire_creates_new_connection_when_needed(self, mock_connection_pool):
        """Test that acquiring a connection creates a new one when needed."""
        pool, create_connection, _, _, test_connection = mock_connection_pool
        
        # Create a second test connection
        test_connection2 = MagicMock()
        create_connection.return_value = test_connection2
        
        # Acquire the first connection
        conn1 = await pool.acquire()
        assert conn1 == test_connection
        
        # Acquire a second connection (should create a new one)
        conn2 = await pool.acquire()
        assert conn2 == test_connection2
        
        # Check stats
        stats = pool.get_stats()
        assert stats["total_connections"] == 2
        assert stats["busy_connections"] == 2
        assert stats["idle_connections"] == 0
        
        # Check that create_connection was called twice
        assert create_connection.call_count == 2
        
        # Release the connections
        await pool.release(conn1)
        await pool.release(conn2)
    
    @pytest.mark.asyncio
    async def test_acquire_timeout(self, mock_connection_pool):
        """Test that acquiring a connection times out when all are busy."""
        pool, _, _, _, test_connection = mock_connection_pool
        
        # Acquire all available connections
        for _ in range(3):  # max_size is 3
            await pool.acquire()
        
        # Try to acquire another connection (should timeout)
        with pytest.raises(ModelTimeoutError):
            await pool.acquire(timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_mark_unhealthy(self, mock_connection_pool):
        """Test marking a connection as unhealthy."""
        pool, _, _, _, test_connection = mock_connection_pool
        
        # Acquire a connection
        conn = await pool.acquire()
        
        # Mark it as unhealthy
        await pool.mark_unhealthy(conn)
        
        # Release the connection
        await pool.release(conn)
        
        # Check stats
        stats = pool.get_stats()
        assert stats["unhealthy_connections"] == 1
        assert stats["idle_connections"] == 0
        
        # Wait for maintenance to close the unhealthy connection and create a new one
        await asyncio.sleep(1.0)
        
        # Check stats again
        stats = pool.get_stats()
        assert stats["unhealthy_connections"] == 0
        assert stats["idle_connections"] == 1
    
    @pytest.mark.asyncio
    async def test_maintenance_closes_idle_connections(self, mock_connection_pool):
        """Test that maintenance closes idle connections that exceed max_idle_time."""
        pool, create_connection, _, _, _ = mock_connection_pool
        
        # Create additional connections to exceed min_size
        test_connection2 = MagicMock()
        create_connection.return_value = test_connection2
        conn2 = await pool.acquire()
        await pool.release(conn2)
        
        # Check stats
        stats = pool.get_stats()
        assert stats["total_connections"] == 2
        assert stats["idle_connections"] == 2
        
        # Wait for maintenance to close idle connections
        await asyncio.sleep(1.5)  # Longer than max_idle_time
        
        # Check stats again
        stats = pool.get_stats()
        assert stats["total_connections"] == 1  # min_size
        assert stats["idle_connections"] == 1
    
    @pytest.mark.asyncio
    async def test_health_check_during_maintenance(self, mock_connection_pool):
        """Test that health checks are performed during maintenance."""
        pool, _, health_check, _, test_connection = mock_connection_pool
        
        # Wait for a health check to occur
        await asyncio.sleep(1.0)  # Longer than health_check_interval
        
        # Check that health_check was called
        health_check.assert_called_with(test_connection)
    
    @pytest.mark.asyncio
    async def test_unhealthy_connection_closed_during_maintenance(self, mock_connection_pool):
        """Test that unhealthy connections are closed during maintenance."""
        pool, create_connection, health_check, close_connection, test_connection = mock_connection_pool
        
        # Make health check return False
        health_check.return_value = False
        
        # Wait for a health check to occur
        await asyncio.sleep(1.0)  # Longer than health_check_interval
        
        # Check that close_connection was called
        close_connection.assert_called_with(test_connection)
        
        # Check that a new connection was created
        assert create_connection.call_count > 1