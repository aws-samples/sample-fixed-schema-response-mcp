"""
Tests for the model manager module.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from fixed_schema_mcp_server.model.model_manager import ModelManager
from fixed_schema_mcp_server.model.model_connector import ModelConnector
from fixed_schema_mcp_server.model.exceptions import ModelError, ModelConnectionError


class MockModelConnector(ModelConnector):
    """Mock implementation of ModelConnector for testing."""
    
    def __init__(self, api_key, model_name="mock-model", default_parameters=None):
        self._api_key = api_key
        self._model_name = model_name
        self._default_parameters = default_parameters or {
            "temperature": 0.5,
            "max_tokens": 100
        }
    
    async def generate(self, prompt, parameters=None):
        merged_params = self.merge_parameters(parameters)
        if "fail" in prompt.lower():
            raise ModelError("Mock error for testing")
        return f"Mock response for: {prompt[:20]}... with temp={merged_params.get('temperature')}"
    
    def get_default_parameters(self):
        return self._default_parameters.copy()
    
    def update_parameters(self, parameters):
        self._default_parameters.update(parameters)
    
    def get_provider_name(self):
        return "mock-provider"
    
    def get_model_name(self):
        return self._model_name
    
    async def health_check(self):
        return True, None


class TestModelManager:
    """Test cases for the ModelManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Return a mock configuration dictionary."""
        return {
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "test-api-key",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    
    @pytest.fixture
    def model_manager(self, mock_config):
        """Return a ModelManager instance with a mocked connector."""
        with patch.object(ModelManager, '_connector_registry', {"openai": MockModelConnector}):
            manager = ModelManager(mock_config)
            return manager
    
    def test_initialization(self, model_manager):
        """Test initializing the model manager."""
        assert model_manager._connector is not None
        assert model_manager._connector.get_provider_name() == "mock-provider"
        assert model_manager._connector.get_model_name() == "gpt-4"
    
    def test_initialization_error(self, mock_config):
        """Test error handling during initialization."""
        # Test missing API key
        config_without_key = mock_config.copy()
        del config_without_key["api_key"]
        
        with pytest.raises(ModelConnectionError):
            with patch.object(ModelManager, '_connector_registry', {"openai": MockModelConnector}):
                ModelManager(config_without_key)
        
        # Test unsupported provider
        config_with_unsupported = mock_config.copy()
        config_with_unsupported["provider"] = "unsupported"
        
        with pytest.raises(ModelConnectionError):
            ModelManager(config_with_unsupported)
    
    @pytest.mark.asyncio
    async def test_generate_response(self, model_manager):
        """Test generating a response."""
        response = await model_manager.generate_response("Test prompt")
        assert "Mock response for: Test prompt" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_with_parameters(self, model_manager):
        """Test generating a response with custom parameters."""
        response = await model_manager.generate_response("Test prompt", {"temperature": 0.8})
        assert "with temp=0.8" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_error(self, model_manager):
        """Test error handling during response generation."""
        with pytest.raises(ModelError):
            await model_manager.generate_response("This should fail")
    
    def test_set_model_parameters(self, model_manager):
        """Test setting model parameters."""
        model_manager.set_model_parameters({"temperature": 0.9, "max_tokens": 200})
        params = model_manager._connector.get_default_parameters()
        assert params["temperature"] == 0.9
        assert params["max_tokens"] == 200
    
    def test_get_model_info(self, model_manager):
        """Test getting model information."""
        info = model_manager.get_model_info()
        assert info["provider"] == "mock-provider"
        assert info["model"] == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_check_model_health(self, model_manager):
        """Test checking model health."""
        health = await model_manager.check_model_health()
        assert health["healthy"] is True
        assert health["provider"] == "mock-provider"
        assert health["model"] == "gpt-4"
        assert health["error"] is None
    
    @pytest.mark.asyncio
    async def test_check_model_health_error(self, model_manager):
        """Test checking model health with error."""
        model_manager._connector.health_check = AsyncMock(side_effect=Exception("Health check failed"))
        
        health = await model_manager.check_model_health()
        assert health["healthy"] is False
        assert "Health check failed" in health["error"]
    
    def test_register_connector(self):
        """Test registering a new connector."""
        # Save original registry
        original_registry = ModelManager._connector_registry.copy()
        
        try:
            # Register a new connector
            ModelManager.register_connector("test", MockModelConnector)
            assert "test" in ModelManager._connector_registry
            assert ModelManager._connector_registry["test"] == MockModelConnector
            
            # Check that it appears in supported providers
            assert "test" in ModelManager.get_supported_providers()
        finally:
            # Restore original registry
            ModelManager._connector_registry = original_registry