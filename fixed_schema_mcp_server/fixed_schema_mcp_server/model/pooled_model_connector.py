"""
Pooled model connector implementations for the Fixed Schema Response MCP Server.

This module provides model connector implementations that use connection pooling
for improved performance and reliability.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Union, Tuple

try:
    import openai
except ImportError:
    openai = None

from fixed_schema_mcp_server.model.model_connector import ModelConnector
from fixed_schema_mcp_server.model.connection_pool import ConnectionPool
from fixed_schema_mcp_server.model.exceptions import (
    ModelError,
    ModelConnectionError,
    ModelResponseError,
    ModelTimeoutError,
    ModelRateLimitError,
    ModelAuthenticationError,
)

logger = logging.getLogger(__name__)


class PooledOpenAIModelConnector(ModelConnector):
    """
    Pooled model connector for OpenAI API.
    
    This class implements the ModelConnector interface for the OpenAI API
    with connection pooling for improved performance and reliability.
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4",
        default_parameters: Optional[Dict[str, Any]] = None,
        pool_size: int = 5,
        max_pool_size: int = 10
    ):
        """
        Initialize the pooled OpenAI model connector.
        
        Args:
            api_key: The OpenAI API key
            model_name: The name of the model to use
            default_parameters: Optional default parameters for the model
            pool_size: The minimum number of connections to maintain in the pool
            max_pool_size: The maximum number of connections allowed in the pool
        """
        self._api_key = api_key
        self._model_name = model_name
        self._default_parameters = default_parameters or {
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 1000,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        self._pool_size = pool_size
        self._max_pool_size = max_pool_size
        self._connection_pool = None
        self._setup_connection_pool()
    
    def _setup_connection_pool(self) -> None:
        """
        Set up the connection pool.
        
        Raises:
            ModelConnectionError: If there is an error setting up the connection pool
        """
        try:
            self._connection_pool = ConnectionPool(
                create_connection=self._create_client,
                health_check=self._check_client_health,
                close_connection=self._close_client,
                min_size=self._pool_size,
                max_size=self._max_pool_size,
                max_idle_time=300.0,  # 5 minutes
                health_check_interval=60.0  # 1 minute
            )
            logger.info(f"OpenAI connection pool initialized for model {self._model_name}")
        except Exception as e:
            raise ModelConnectionError(
                f"Failed to initialize OpenAI connection pool: {str(e)}",
                provider="openai",
                cause=e
            )
    
    async def _create_client(self):
        """
        Create a new OpenAI client.
        
        Returns:
            A new OpenAI client
            
        Raises:
            ModelConnectionError: If there is an error creating the client
        """
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self._api_key)
            logger.debug(f"Created new OpenAI client for model {self._model_name}")
            return client
        except ImportError:
            raise ModelConnectionError(
                "OpenAI package not installed. Install it with 'pip install openai'.",
                provider="openai"
            )
        except Exception as e:
            raise ModelConnectionError(
                f"Failed to create OpenAI client: {str(e)}",
                provider="openai",
                cause=e
            )
    
    async def _check_client_health(self, client) -> bool:
        """
        Check if an OpenAI client is healthy.
        
        Args:
            client: The OpenAI client to check
            
        Returns:
            True if the client is healthy, False otherwise
        """
        try:
            # Make a simple models.list request to check API access
            await client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI client health check failed: {e}")
            return False
    
    async def _close_client(self, client) -> None:
        """
        Close an OpenAI client.
        
        Args:
            client: The OpenAI client to close
        """
        # OpenAI clients don't need explicit closing, but we'll log it
        logger.debug("Closed OpenAI client")
    
    async def start(self) -> None:
        """Start the connection pool."""
        if self._connection_pool:
            await self._connection_pool.start()
    
    async def stop(self) -> None:
        """Stop the connection pool."""
        if self._connection_pool:
            await self._connection_pool.stop()
    
    async def generate(self, prompt: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response from the OpenAI model.
        
        Args:
            prompt: The prompt to send to the model
            parameters: Optional model parameters to override defaults
            
        Returns:
            The generated response as a string
            
        Raises:
            ModelConnectionError: If there is an error connecting to the OpenAI API
            ModelResponseError: If there is an error processing the model response
            ModelTimeoutError: If the model request times out
            ModelRateLimitError: If the OpenAI API rate limit is exceeded
            ModelAuthenticationError: If there is an authentication error
        """
        if not self._connection_pool:
            self._setup_connection_pool()
            await self._connection_pool.start()
        
        merged_params = self.merge_parameters(parameters)
        client = None
        
        try:
            # Acquire a client from the pool
            client = await self._connection_pool.acquire()
            
            # Make the API call
            response = await client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                **merged_params
            )
            
            if not response.choices or len(response.choices) == 0:
                raise ModelResponseError("No choices returned from OpenAI API")
            
            # Release the client back to the pool
            await self._connection_pool.release(client)
            client = None  # Prevent double release in finally block
            
            return response.choices[0].message.content
            
        except openai.RateLimitError as e:
            # Mark the client as unhealthy
            if client:
                await self._connection_pool.mark_unhealthy(client)
                client = None  # Prevent release in finally block
            
            retry_after = None
            if hasattr(e, 'retry_after'):
                retry_after = e.retry_after
            raise ModelRateLimitError(
                str(e),
                provider="openai",
                retry_after=retry_after
            )
        except openai.AuthenticationError as e:
            # Mark the client as unhealthy
            if client:
                await self._connection_pool.mark_unhealthy(client)
                client = None  # Prevent release in finally block
            
            raise ModelAuthenticationError(
                str(e),
                provider="openai"
            )
        except asyncio.TimeoutError as e:
            # Mark the client as unhealthy
            if client:
                await self._connection_pool.mark_unhealthy(client)
                client = None  # Prevent release in finally block
            
            raise ModelTimeoutError(
                "Request to OpenAI API timed out",
                timeout=merged_params.get("timeout")
            )
        except Exception as e:
            # Mark the client as unhealthy for any other error
            if client:
                await self._connection_pool.mark_unhealthy(client)
                client = None  # Prevent release in finally block
            
            if openai and isinstance(e, openai.APIError):
                raise ModelConnectionError(
                    f"OpenAI API error: {str(e)}",
                    provider="openai",
                    cause=e
                )
            
            # Convert any other exception to a ModelResponseError
            if not isinstance(e, ModelError):  # Avoid re-wrapping ModelErrors
                raise ModelResponseError(
                    f"Error generating response from OpenAI: {str(e)}",
                    cause=e
                )
            raise  # Re-raise ModelErrors as-is
        finally:
            # Release the client back to the pool if it wasn't already released
            if client:
                try:
                    await self._connection_pool.release(client)
                except Exception as e:
                    logger.error(f"Error releasing client to pool: {e}")
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get the default parameters for the OpenAI model.
        
        Returns:
            A dictionary of default parameters
        """
        return self._default_parameters.copy()
    
    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Update the OpenAI model parameters.
        
        Args:
            parameters: The parameters to update
        """
        self._default_parameters.update(parameters)
    
    def get_provider_name(self) -> str:
        """
        Get the name of the model provider.
        
        Returns:
            The string "openai"
        """
        return "openai"
    
    def get_model_name(self) -> str:
        """
        Get the name of the OpenAI model being used.
        
        Returns:
            The name of the model (e.g., "gpt-4")
        """
        return self._model_name
    
    async def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Check if the OpenAI API is healthy and accessible.
        
        Returns:
            A tuple containing:
            - A boolean indicating whether the API is healthy
            - An optional string with an error message if the API is not healthy
        """
        if not self._connection_pool:
            try:
                self._setup_connection_pool()
                await self._connection_pool.start()
            except ModelError as e:
                return False, str(e)
        
        try:
            # Get connection pool stats
            stats = self._connection_pool.get_stats()
            
            # If there are no healthy connections, the API is not healthy
            if stats["total_connections"] == 0 or stats["total_connections"] == stats["unhealthy_connections"]:
                return False, "No healthy connections in the pool"
            
            return True, None
        except Exception as e:
            return False, f"OpenAI API health check failed: {str(e)}"
    
    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the connection pool.
        
        Returns:
            A dictionary containing statistics about the connection pool
        """
        if not self._connection_pool:
            return {"error": "Connection pool not initialized"}
        
        return self._connection_pool.get_stats()