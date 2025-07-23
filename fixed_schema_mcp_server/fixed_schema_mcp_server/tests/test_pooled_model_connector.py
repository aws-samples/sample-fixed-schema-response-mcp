"""
Tests for the pooled model connector module.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fixed_schema_mcp_server.model.pooled_model_connector import PooledOpenAIModelConnector
from fixed_schema_mcp_server.model.exceptions import (
    ModelConnectionError,
    ModelResponseError,
    ModelTimeoutError,
    ModelRateLimitError,
    ModelAuthenticationError,
)


class TestPooledOpenAIModelConnector:
    """Test cases for the PooledOpenAIModelConnector class."""
    
    @pytest.fixture
    async def mock_connector(self):
        """Create a mock pooled OpenAI connector for testing."""
        # Create a mock connector with a mock connection pool
        with patch('fixed_schema_mcp_server.model.pooled_model_connector.ConnectionPool') as mock_pool_class:
            # Create mock pool instance
            mock_pool = MagicMock()
            mock_pool.start = AsyncMock()
            mock_pool.stop = AsyncMock()
            mock_pool.acquire = AsyncMock()
            mock_pool.release = AsyncMock()
            mock_pool.mark_unhealthy = AsyncMock()
            mock_pool.get_stats = MagicMock(return_value={
                "total_connections": 5,
                "idle_connections": 3,
                "busy_connections": 2,
                "unhealthy_connections": 0
            })
            
            # Make the pool class return our mock pool
            mock_pool_class.return_value = mock_pool
            
            # Create the connector
            connector = PooledOpenAIModelConnector(
                api_key="test_api_key",
                model_name="test-model",
                pool_size=3,
                max_pool_size=5
            )
            
            # Start the connector
            await connector.start()
            
            # Return the connector and mock pool
            yield connector, mock_pool
            
            # Stop the connector
            await connector.stop()
    
    @pytest.mark.asyncio
    async def test_start_stop(self, mock_connector):
        """Test starting and stopping the connector."""
        connector, mock_pool = mock_connector
        
        # Check that the pool was started
        mock_pool.start.assert_called_once()
        
        # Stop the connector
        await connector.stop()
        
        # Check that the pool was stopped
        mock_pool.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_connector):
        """Test generating a response successfully."""
        connector, mock_pool = mock_connector
        
        # Create a mock client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Make the pool return our mock client
        mock_pool.acquire.return_value = mock_client
        
        # Generate a response
        response = await connector.generate("Test prompt")
        
        # Check that the response is correct
        assert response == "Test response"
        
        # Check that the client was acquired and released
        mock_pool.acquire.assert_called_once()
        mock_pool.release.assert_called_once_with(mock_client)
        
        # Check that the client was used correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "test-model"
        assert call_args["messages"][0]["content"] == "Test prompt"
    
    @pytest.mark.asyncio
    async def test_generate_rate_limit_error(self, mock_connector):
        """Test handling a rate limit error."""
        connector, mock_pool = mock_connector
        
        # Create a mock client that raises a rate limit error
        mock_client = MagicMock()
        mock_error = MagicMock(spec=Exception)
        mock_error.__class__.__name__ = "RateLimitError"
        mock_client.chat.completions.create = AsyncMock(side_effect=mock_error)
        
        # Make the pool return our mock client
        mock_pool.acquire.return_value = mock_client
        
        # Generate a response (should raise an error)
        with pytest.raises(ModelRateLimitError):
            await connector.generate("Test prompt")
        
        # Check that the client was acquired and marked unhealthy
        mock_pool.acquire.assert_called_once()
        mock_pool.mark_unhealthy.assert_called_once_with(mock_client)
        
        # Check that the client was not released
        mock_pool.release.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_authentication_error(self, mock_connector):
        """Test handling an authentication error."""
        connector, mock_pool = mock_connector
        
        # Create a mock client that raises an authentication error
        mock_client = MagicMock()
        mock_error = MagicMock(spec=Exception)
        mock_error.__class__.__name__ = "AuthenticationError"
        mock_client.chat.completions.create = AsyncMock(side_effect=mock_error)
        
        # Make the pool return our mock client
        mock_pool.acquire.return_value = mock_client
        
        # Generate a response (should raise an error)
        with pytest.raises(ModelAuthenticationError):
            await connector.generate("Test prompt")
        
        # Check that the client was acquired and marked unhealthy
        mock_pool.acquire.assert_called_once()
        mock_pool.mark_unhealthy.assert_called_once_with(mock_client)
    
    @pytest.mark.asyncio
    async def test_generate_timeout_error(self, mock_connector):
        """Test handling a timeout error."""
        connector, mock_pool = mock_connector
        
        # Create a mock client that raises a timeout error
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=asyncio.TimeoutError())
        
        # Make the pool return our mock client
        mock_pool.acquire.return_value = mock_client
        
        # Generate a response (should raise an error)
        with pytest.raises(ModelTimeoutError):
            await connector.generate("Test prompt")
        
        # Check that the client was acquired and marked unhealthy
        mock_pool.acquire.assert_called_once()
        mock_pool.mark_unhealthy.assert_called_once_with(mock_client)
    
    @pytest.mark.asyncio
    async def test_generate_other_error(self, mock_connector):
        """Test handling other errors."""
        connector, mock_pool = mock_connector
        
        # Create a mock client that raises a generic error
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Test error"))
        
        # Make the pool return our mock client
        mock_pool.acquire.return_value = mock_client
        
        # Generate a response (should raise an error)
        with pytest.raises(ModelResponseError):
            await connector.generate("Test prompt")
        
        # Check that the client was acquired and marked unhealthy
        mock_pool.acquire.assert_called_once()
        mock_pool.mark_unhealthy.assert_called_once_with(mock_client)
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_connector):
        """Test the health check method."""
        connector, mock_pool = mock_connector
        
        # Perform a health check
        is_healthy, error_message = await connector.health_check()
        
        # Check that the health check returned the expected result
        assert is_healthy is True
        assert error_message is None
    
    def test_get_connection_pool_stats(self, mock_connector):
        """Test getting connection pool stats."""
        connector, mock_pool = mock_connector
        
        # Get the stats
        stats = connector.get_connection_pool_stats()
        
        # Check that the stats are correct
        assert stats["total_connections"] == 5
        assert stats["idle_connections"] == 3
        assert stats["busy_connections"] == 2
        assert stats["unhealthy_connections"] == 0