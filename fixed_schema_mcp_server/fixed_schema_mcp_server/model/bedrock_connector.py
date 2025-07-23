"""
Amazon Bedrock model connector for Claude 3.5 Sonnet v2.
"""
import json
import logging
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

from ..core.exceptions import ModelError

logger = logging.getLogger(__name__)

class BedrockModelConnector:
    """Connector for Amazon Bedrock models."""
    
    def __init__(self, model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0", region: Optional[str] = None):
        """
        Initialize the Bedrock model connector.
        
        Args:
            model_id: The Bedrock model ID to use
            region: AWS region (if None, uses the default from AWS config)
        """
        self.model_id = model_id
        self.client = boto3.client('bedrock-runtime', region_name=region)
        logger.info(f"Initialized Bedrock connector with model {model_id}")
    
    async def generate_response(self, prompt: str, system_prompt: str = "", parameters: Dict[str, Any] = None) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: The user prompt
            system_prompt: The system prompt to guide the model
            parameters: Additional parameters for the model
            
        Returns:
            The generated response text
            
        Raises:
            ModelError: If there's an error generating the response
        """
        if parameters is None:
            parameters = {}
        
        # Default parameters
        default_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000
        }
        
        # Merge with user-provided parameters
        for key, value in parameters.items():
            if key in default_params:
                default_params[key] = value
        
        # Prepare the request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": default_params["max_tokens"],
            "temperature": default_params["temperature"],
            "top_p": default_params["top_p"],
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_body["system"] = system_prompt
        
        try:
            # Invoke the model
            logger.debug(f"Sending request to Bedrock: {json.dumps(request_body)}")
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read().decode('utf-8'))
            logger.debug(f"Received response from Bedrock: {json.dumps(response_body)}")
            
            # Extract the generated text
            if 'content' in response_body and len(response_body['content']) > 0:
                for content_item in response_body['content']:
                    if content_item.get('type') == 'text':
                        return content_item.get('text', '')
            
            # If we couldn't find the text in the expected structure
            raise ModelError("Unexpected response format from Bedrock")
            
        except ClientError as e:
            logger.error(f"AWS Bedrock error: {str(e)}")
            raise ModelError(f"Bedrock API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise ModelError(f"Error generating response: {str(e)}")