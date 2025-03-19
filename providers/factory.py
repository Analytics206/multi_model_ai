"""Factory for AI provider instances management."""

from typing import Dict, Optional, Any, List
import asyncio
import logging
from contextlib import asynccontextmanager

from .base import BaseProvider
from . import get_provider

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
        """Get or create a provider instance.
        
        This method reuses existing provider instances when possible to avoid
        creating multiple connections to the same provider.
        
        Args:
            provider_name: The name of the provider
            api_key: The API key for the provider
            organization_id: Optional organization ID
            
        Returns:
            A provider instance
        """
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
                    provider = get_provider(
                        provider_name=provider_name,
                        api_key=api_key,
                        organization_id=organization_id
                    )
                    self._providers[provider_name][provider_key] = provider
                except Exception as e:
                    logger.error(f"Error creating provider {provider_name}: {str(e)}")
                    raise
        
        return self._providers[provider_name][provider_key]
    
    @asynccontextmanager
    async def provider_context(
        self, 
        provider_name: str, 
        api_key: str, 
        organization_id: Optional[str] = None
    ):
        """Context manager for getting a provider instance.
        
        Args:
            provider_name: The name of the provider
            api_key: The API key for the provider
            organization_id: Optional organization ID
            
        Yields:
            A provider instance
        """
        provider = await self.get_provider(
            provider_name=provider_name,
            api_key=api_key,
            organization_id=organization_id
        )
        try:
            yield provider
        finally:
            pass  # No cleanup needed for now
    
    async def list_all_models(
        self,
        api_keys: Dict[str, str],
        organization_ids: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """List all available models from all configured providers.
        
        Args:
            api_keys: Dictionary of provider names to API keys
            organization_ids: Optional dictionary of provider names to organization IDs
            
        Returns:
            List of all available models
        """
        if organization_ids is None:
            organization_ids = {}
            
        all_models = []
        tasks = []
        
        # Create tasks for each provider
        for provider_name, api_key in api_keys.items():
            organization_id = organization_ids.get(provider_name)
            
            async def get_models_for_provider(pname, pkey, org_id):
                try:
                    provider = await self.get_provider(pname, pkey, org_id)
                    models = await provider.get_models()
                    return models
                except Exception as e:
                    logger.error(f"Error getting models for {pname}: {str(e)}")
                    return []
            
            tasks.append(get_models_for_provider(provider_name, api_key, organization_id))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error getting models: {str(result)}")
                continue
                
            if isinstance(result, list):
                all_models.extend(result)
                
        return all_models
    
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
    
    async def calculate_tokens(
        self,
        provider_name: str,
        text: str,
        model: str,
        api_key: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Calculate the number of tokens in the provided text.
        
        Args:
            provider_name: The name of the provider
            text: The text to tokenize
            model: The model to use for tokenization
            api_key: The API key for the provider
            organization_id: Optional organization ID
            
        Returns:
            Dictionary with token count information
        """
        provider = await self.get_provider(
            provider_name=provider_name,
            api_key=api_key,
            organization_id=organization_id
        )
        
        return await provider.calculate_tokens(text=text, model=model)
    
    def get_provider_for_model(self, model_id: str) -> str:
        """Determine the provider based on the model ID.
        
        Args:
            model_id: The model identifier
            
        Returns:
            The name of the provider that offers this model
            
        Raises:
            ValueError: If the provider cannot be determined
        """
        model_id = model_id.lower()
        
        # Check for OpenAI models
        if (model_id.startswith("gpt") or 
            model_id.startswith("text-") or 
            model_id.startswith("davinci") or
            "openai" in model_id):
            return "openai"
            
        # Check for Anthropic models
        if "claude" in model_id or "anthropic" in model_id:
            return "anthropic"
            
        # Check for Google models
        if "gemini" in model_id or "palm" in model_id or "google" in model_id:
            return "google"
            
        # Check for Cohere models
        if "command" in model_id or "cohere" in model_id:
            return "cohere"
            
        # If we can't determine the provider, raise an error
        raise ValueError(f"Cannot determine provider for model: {model_id}")
    
    async def run_with_rate_limit_handling(
        self,
        coro,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ) -> Any:
        """Execute a coroutine with rate limit handling.
        
        Args:
            coro: The coroutine to execute
            max_retries: Maximum number of retries
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            
        Returns:
            The result of the coroutine
            
        Raises:
            Exception: If the coroutine fails after all retries
        """
        retries = 0
        last_exception = None
        
        while retries <= max_retries:
            try:
                return await coro
            except Exception as e:
                last_exception = e
                
                # Check if this is a rate limit error
                error_type = type(e).__name__
                error_message = str(e).lower()
                
                is_rate_limit = (
                    "rate" in error_message or 
                    "limit" in error_message or
                    "capacity" in error_message or
                    "429" in error_message or
                    "too many" in error_message or
                    "rateLimitError" in error_type
                )
                
                if not is_rate_limit or retries >= max_retries:
                    # Not a rate limit error or out of retries
                    raise
                
                # Calculate exponential backoff
                delay = min(base_delay * (2 ** retries), max_delay)
                
                # Jitter: Randomize the delay slightly to avoid thundering herd
                jitter = delay * 0.1  # 10% jitter
                delay = delay + (jitter * (2 * asyncio.Random().random() - 1))
                
                logger.warning(
                    f"Rate limited by provider. Retrying in {delay:.2f}s... "
                    f"(Attempt {retries + 1}/{max_retries})"
                )
                
                await asyncio.sleep(delay)
                retries += 1
        
        # If we've exhausted all retries
        if last_exception:
            raise last_exception