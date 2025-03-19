"""Provider module for AI model integrations.

This module provides a consistent interface for interacting with different
AI model providers like OpenAI, Anthropic, Google, and Cohere.
"""

from typing import Dict, Type, Any, Optional
import logging

from .base import BaseProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .cohere import CohereProvider
from .factory import ProviderFactory

logger = logging.getLogger(__name__)

# Registry of available providers
PROVIDER_REGISTRY: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "cohere": CohereProvider,
}

# Singleton factory instance
factory = ProviderFactory()

def get_provider(
    provider_name: str, 
    api_key: str, 
    organization_id: Optional[str] = None
) -> BaseProvider:
    """Get a provider instance by name.
    
    Args:
        provider_name: The name of the provider to instantiate
        api_key: The API key for authentication
        organization_id: Optional organization ID for providers that support it
        
    Returns:
        An instance of the requested provider
        
    Raises:
        ValueError: If the provider is not supported
    """
    provider_class = PROVIDER_REGISTRY.get(provider_name.lower())
    
    if not provider_class:
        raise ValueError(f"Provider '{provider_name}' is not supported. "
                         f"Available providers: {list(PROVIDER_REGISTRY.keys())}")
    
    return provider_class(api_key=api_key, organization_id=organization_id)

def list_available_providers() -> Dict[str, Dict[str, Any]]:
    """List all available provider configurations.
    
    Returns:
        A dictionary of provider names and their configurations
    """
    providers_info = {}
    
    for provider_name, provider_class in PROVIDER_REGISTRY.items():
        providers_info[provider_name] = {
            "name": provider_name,
            "class": provider_class.__name__,
            "description": provider_class.__doc__.strip() if provider_class.__doc__ else None
        }
    
    return providers_info

__all__ = [
    'BaseProvider',
    'OpenAIProvider',
    'AnthropicProvider',
    'GoogleProvider',
    'CohereProvider',
    'ProviderFactory',
    'factory',
    'get_provider',
    'list_available_providers',
    'PROVIDER_REGISTRY'
]