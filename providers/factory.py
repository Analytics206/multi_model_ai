"""Factory for AI provider instances management."""

from typing import Dict, Optional, Any, List
import asyncio
import logging
from contextlib import asynccontextmanager

from .base import BaseProvider

logger = logging.getLogger(__name__)

class ProviderFactory:
    """Factory for managing AI provider instances."""
    
    def __init__(self):
        """Initialize the provider factory."""
        self._providers: Dict[str, Dict[str, BaseProvider]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
    
    async def get_provider(
        self, 
        provider_name: str, 
        api_key: str, 
        organization_id: Optional[str] = None
    ) -> BaseProvider:
        """Get or create a provider instance."""
        from . import get_provider as create_provider
        
        provider_key = f"{provider_name}:{api_key}:{organization_id or ''}"
        
        # Create a lock for this provider if it doesn't exist
        if provider_name not in self._locks:
            self._locks[provider_name] = asyncio.Lock()
        
        # Use a lock to prevent race conditions when creating providers
        async with self._locks[provider_name]:
            # Initialize provider dict for this provider if it doesn't exist
            if provider_name not in self._providers:
                self._providers[provider_name] = {}
                
            # Create and store the provider if it doesn't exist
            if provider_key not in self._providers[provider_name]:
                try:
                    logger.debug(f"Creating new {provider_name} provider instance")
                    provider = create_provider(
                        provider_name=provider_name,
                        api_key=api_key,
                        organization_id=organization_id
                    )
                    self._providers[provider_name][provider_key] = provider
                except Exception as e:
                    logger.error(f"Error creating provider {provider_name}: {str(e)}")
                    raise
        
        return self._providers[provider_name][provider_key]
    
    async def generate_completion(
        self,
        provider_name: str,
        model: str,
        messages: List[Dict[str, str]],
        api_key: str,
        organization_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        stream: bool = False,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Generate a completion using the specified provider and model.
        
        Args:
            provider_name: The name of the provider
            model: The model identifier
            messages: List of message dictionaries
            api_key: The API key for the provider
            organization_id: Optional organization ID
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop_sequences: Sequences where generation should stop
            presence_penalty: Penalty for token repetition
            frequency_penalty: Penalty for frequency of token repetition
            stream: Whether to stream the response
            additional_params: Additional provider-specific parameters
            
        Returns:
            Either a completion response dict or an async generator for streaming
        """
        provider = await self.get_provider(
            provider_name=provider_name,
            api_key=api_key,
            organization_id=organization_id
        )
        
        if stream:
            return provider.generate_completion_stream(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=stop_sequences,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                additional_params=additional_params
            )
        else:
            return await provider.generate_completion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=stop_sequences,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                additional_params=additional_params
            )
        # Include the rest of your implementation...
        # (Keep all the other methods from the original factory.py)