"""
Factory for creating model connectors based on configuration.
"""
import logging
import os
from typing import Dict, Any

from ..core.exceptions import ConfigurationError
from .bedrock_connector import BedrockModelConnector
from .mock_connector import MockModelConnector

logger = logging.getLogger(__name__)

class ModelFactory:
    """Factory for creating model connectors."""
    
    @staticmethod
    def create_model_connector(config: Dict[str, Any]):
        """
        Create a model connector based on the configuration.
        
        Args:
            config: The model configuration
            
        Returns:
            A model connector instance
            
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        provider = config.get("provider", "").lower()
        
        # Check if we should use the mock connector
        use_mock = os.environ.get("USE_MOCK_MODEL", "").lower() in ("true", "1", "yes")
        
        if use_mock:
            logger.info("Using mock model connector as specified by USE_MOCK_MODEL environment variable")
            return MockModelConnector(model_id=config.get("model_id", "mock-model"))
        
        if provider == "bedrock":
            model_id = config.get("model_id", "anthropic.claude-3-5-sonnet-20240620-v1:0")
            region = config.get("region")
            
            try:
                # Try to create the Bedrock connector
                logger.info(f"Creating Bedrock model connector with model {model_id}")
                return BedrockModelConnector(model_id=model_id, region=region)
            except Exception as e:
                # If there's an error (e.g., no AWS credentials), fall back to the mock connector
                logger.warning(f"Failed to create Bedrock connector: {e}. Falling back to mock connector.")
                return MockModelConnector(model_id=f"mock-{model_id}")
        elif provider == "mock":
            # Explicitly configured mock provider
            model_id = config.get("model_id", "mock-model")
            logger.info(f"Creating mock model connector with model {model_id}")
            return MockModelConnector(model_id=model_id)
        else:
            raise ConfigurationError(f"Unsupported model provider: {provider}")