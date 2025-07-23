"""
Mock model connector for testing purposes.
"""
import json
import logging
from typing import Dict, Any, Optional

from ..core.exceptions import ModelError

logger = logging.getLogger(__name__)

class MockModelConnector:
    """Mock connector for testing without a real model API."""
    
    def __init__(self, model_id: str = "mock-model", **kwargs):
        """
        Initialize the mock model connector.
        
        Args:
            model_id: A mock model ID
            **kwargs: Additional arguments (ignored)
        """
        self.model_id = model_id
        logger.info(f"Initialized mock connector with model {model_id}")
    
    async def generate_response(self, prompt: str, system_prompt: str = "", parameters: Dict[str, Any] = None) -> str:
        """
        Generate a mock response based on the prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: The system prompt to guide the model
            parameters: Additional parameters for the model
            
        Returns:
            A mock response in JSON format
            
        Raises:
            ModelError: If there's an error generating the response
        """
        try:
            logger.info(f"Generating mock response for prompt: {prompt[:100]}...")
            logger.info(f"System prompt: {system_prompt}")
            
            # Extract schema information from the parameters
            schema_name = parameters.get("schema") if parameters else None
            
            # If schema name is not in parameters, try to extract it from the prompt or system prompt
            if not schema_name:
                if "product_info" in prompt.lower() or (system_prompt and "product_info" in system_prompt.lower()):
                    schema_name = "product_info"
                elif "article_summary" in prompt.lower() or (system_prompt and "article_summary" in system_prompt.lower()):
                    schema_name = "article_summary"
            
            # Generate response based on schema
            if schema_name == "product_info" or "product_info" in prompt.lower():
                return self._generate_product_info_response(prompt)
            elif schema_name == "article_summary" or "article_summary" in prompt.lower():
                return self._generate_article_summary_response(prompt)
            else:
                # Check for specific keywords in the prompt
                if "iphone" in prompt.lower():
                    return self._generate_product_info_response(prompt)
                elif "ai" in prompt.lower() or "artificial intelligence" in prompt.lower():
                    return self._generate_article_summary_response(prompt)
                else:
                    # Default response
                    return json.dumps({
                        "message": "This is a mock response. Please specify a schema in your prompt."
                    })
                
        except Exception as e:
            logger.error(f"Error generating mock response: {str(e)}")
            raise ModelError(f"Error generating mock response: {str(e)}")
    
    def _generate_product_info_response(self, prompt: str) -> str:
        """Generate a mock product info response."""
        if "iphone" in prompt.lower():
            return json.dumps({
                "name": "iPhone 15 Pro",
                "description": "The latest flagship smartphone from Apple featuring a powerful A17 Pro chip, a stunning Super Retina XDR display, and an advanced camera system.",
                "price": 999.99,
                "category": "Smartphones",
                "features": [
                    "A17 Pro chip",
                    "48MP main camera",
                    "Titanium design",
                    "Action button",
                    "USB-C connector"
                ]
            })
        else:
            return json.dumps({
                "name": "Generic Product",
                "description": "This is a generic product description.",
                "price": 99.99,
                "category": "Electronics",
                "features": [
                    "Feature 1",
                    "Feature 2",
                    "Feature 3"
                ]
            })
    
    def _generate_article_summary_response(self, prompt: str) -> str:
        """Generate a mock article summary response."""
        if "ai" in prompt.lower():
            return json.dumps({
                "title": "Recent Advancements in Artificial Intelligence",
                "summary": "The field of AI has seen significant advancements in the past year, with breakthroughs in large language models, computer vision, and reinforcement learning.",
                "key_points": [
                    "New multimodal models combine text, image, and audio understanding",
                    "Smaller, more efficient models are being developed for edge devices",
                    "AI safety and alignment research is gaining more attention",
                    "Open-source AI models are becoming more competitive with proprietary ones"
                ],
                "sentiment": "positive"
            })
        else:
            return json.dumps({
                "title": "Generic Article",
                "summary": "This is a summary of a generic article.",
                "key_points": [
                    "Key point 1",
                    "Key point 2",
                    "Key point 3"
                ],
                "sentiment": "neutral"
            })