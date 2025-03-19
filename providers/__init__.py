"""Provider module for AI model integrations."""

from typing import Dict, Type, Any, Optional
import logging

from .base import BaseProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .factory import ProviderFactory

logger = logging.getLogger(__name__)

# Registry of available providers
PROVIDER_REGISTRY: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

# Singleton factory instance
factory = ProviderFactory()

def get_provider(
    provider_name: str, 
    api_key: str, 
    organization_id: Optional[str] = None
) -> BaseProvider:
    """Get a provider instance by name."""
    provider_class = PROVIDER_REGISTRY.get(provider_name.lower())
    
    if not provider_class:
        raise ValueError(f"Provider '{provider_name}' is not supported. "
                         f"Available providers: {list(PROVIDER_REGISTRY.keys())}")
    
    return provider_class(api_key=api_key, organization_id=organization_id)

__all__ = [
    'BaseProvider', 
    'OpenAIProvider', 
    'AnthropicProvider',
    'ProviderFactory', 
    'factory', 
    'get_provider',
    'PROVIDER_REGISTRY'
]