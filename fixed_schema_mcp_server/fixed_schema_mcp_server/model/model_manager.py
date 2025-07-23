"""
Model manager implementation for the Fixed Schema Response MCP Server.
"""
import logging
from typing import Dict, Any, Optional

from ..core.interfaces import ModelManagerInterface
from ..core.exceptions import ConfigurationError, ModelError
from .model_factory import ModelFactory

logger = logging.getLogger(__name__)

class ModelManager(ModelManagerInterface):
    """Model manager implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the model manager.
        
        Args:
            config: The model configuration
            
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        self._config = config
        self._default_parameters = config.get("parameters", {})
        
        try:
            # Create the model connector
            self._model_connector = ModelFactory.create_model_connector(config)
            logger.info("Model manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing model manager: {str(e)}")
            raise ConfigurationError(f"Error initializing model manager: {str(e)}")
    
    async def start(self) -> None:
        """Start the model manager."""
        logger.info("Model manager started")
    
    async def stop(self) -> None:
        """Stop the model manager."""
        logger.info("Model manager stopped")
    
    async def generate_response(self, prompt: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            parameters: Optional model parameters to override defaults
            
        Returns:
            The generated response as a string
            
        Raises:
            ModelError: If there's an error generating the response
        """
        try:
            # Merge default parameters with provided parameters
            merged_parameters = self._default_parameters.copy()
            if parameters:
                merged_parameters.update(parameters)
            
            # Extract system prompt if present in the parameters
            system_prompt = merged_parameters.pop("system_prompt", "")
            
            # Generate the response
            logger.debug(f"Generating response with prompt: {prompt[:100]}...")
            response = await self._model_connector.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                parameters=merged_parameters
            )
            
            logger.debug(f"Generated response: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise ModelError(f"Error generating response: {str(e)}")
    
    def set_model_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Update model parameters.
        
        Args:
            parameters: The parameters to update
        """
        self._default_parameters.update(parameters)
        logger.debug(f"Updated model parameters: {parameters}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            A dictionary containing model information
        """
        provider = self._config.get("provider", "unknown")
        model_id = self._config.get("model_id", "unknown")
        
        return {
            "provider": provider,
            "model": model_id
        }
    
    async def check_model_health(self) -> Dict[str, Any]:
        """
        Check the health of the model.
        
        Returns:
            A dictionary containing health information
        """
        return {
            "status": "healthy",
            "provider": self._config.get("provider", "unknown"),
            "model": self._config.get("model_id", "unknown")
        }