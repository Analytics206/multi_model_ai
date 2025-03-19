from typing import Dict, List, Any, Optional, AsyncGenerator
import logging
import tiktoken
from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
import asyncio
from contextlib import asynccontextmanager

from .base import BaseProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""
    
    def _setup_client(self) -> None:
        """Set up the OpenAI API client."""
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.organization_id
        )
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Retrieve available models from OpenAI.
        
        Returns:
            A list of dictionaries containing model information
        """
        try:
            response = await self._client.models.list()
            models = []
            
            # Filter for chat/completion models
            for model in response.data:
                # Only include GPT models and other text generation models
                if (
                    model.id.startswith("gpt") or 
                    "text-" in model.id or
                    "davinci" in model.id
                ):
                    models.append({
                        "id": model.id,
                        "name": model.id,
                        "provider": "openai",
                        "created": model.created,
                        "owned_by": model.owned_by
                    })
            
            return models
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {str(e)}")
            return await self.handle_provider_error(e)
    
    async def generate_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a text completion from OpenAI.
        
        Args:
            model: The model identifier to use
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter (alternative to temperature)
            stop_sequences: List of sequences where generation should stop
            presence_penalty: Penalty for token repetition
            frequency_penalty: Penalty for frequency of token repetition
            additional_params: Additional provider-specific parameters
            
        Returns:
            A dictionary containing the completion response
        """
        try:
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences is not None:
                params["stop"] = stop_sequences
            if presence_penalty is not None:
                params["presence_penalty"] = presence_penalty
            if frequency_penalty is not None:
                params["frequency_penalty"] = frequency_penalty
            
            # Add any additional params provided
            if additional_params:
                params.update(additional_params)
            
            response = await self._client.chat.completions.create(**params)
            
            # Format the response in a standardized way
            result = {
                "id": response.id,
                "model": response.model,
                "created": response.created,
                "provider": "openai",
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            return result
        
        except (APIError, RateLimitError, APIConnectionError) as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return await self.handle_provider_error(e)
        except Exception as e:
            logger.error(f"Unexpected error with OpenAI: {str(e)}")
            return await self.handle_provider_error(e)
    
    async def generate_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a streaming text completion from OpenAI.
        
        Args:
            model: The model identifier to use
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter (alternative to temperature)
            stop_sequences: List of sequences where generation should stop
            presence_penalty: Penalty for token repetition
            frequency_penalty: Penalty for frequency of token repetition
            additional_params: Additional provider-specific parameters
            
        Returns:
            An async generator yielding completion chunks
        """
        try:
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            }
            
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences is not None:
                params["stop"] = stop_sequences
            if presence_penalty is not None:
                params["presence_penalty"] = presence_penalty
            if frequency_penalty is not None:
                params["frequency_penalty"] = frequency_penalty
            
            # Add any additional params provided
            if additional_params:
                params.update(additional_params)
            
            stream = await self._client.chat.completions.create(**params)
            
            # Stream response chunks
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    # Format each chunk in a standardized way
                    yield {
                        "id": chunk.id,
                        "model": chunk.model,
                        "created": chunk.created,
                        "provider": "openai",
                        "content": delta.content or "",
                        "role": delta.role if hasattr(delta, "role") else None,
                        "finish_reason": chunk.choices[0].finish_reason,
                        "is_chunk": True
                    }
        
        except (APIError, RateLimitError, APIConnectionError) as e:
            logger.error(f"OpenAI streaming API error: {str(e)}")
            yield await self.handle_provider_error(e)
        except Exception as e:
            logger.error(f"Unexpected error with OpenAI streaming: {str(e)}")
            yield await self.handle_provider_error(e)
    
    async def calculate_tokens(self, text: str, model: str) -> Dict[str, int]:
        """Calculate the number of tokens in the provided text.
        
        Args:
            text: The text to tokenize
            model: The model to use for tokenization
            
        Returns:
            Dictionary with token count information
        """
        try:
            # Get the encoding for the specified model
            encoding = None
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base encoding (used by gpt-4, gpt-3.5-turbo)
                encoding = tiktoken.get_encoding("cl100k_base")
            
            tokens = encoding.encode(text)
            
            return {
                "token_count": len(tokens),
                "model": model,
                "provider": "openai"
            }
        except Exception as e:
            logger.error(f"Error calculating tokens: {str(e)}")
            return {
                "error": True,
                "error_type": type(e).__name__,
                "message": str(e),
                "provider": "openai"
            }
    
    async def handle_provider_error(self, error: Exception) -> Dict[str, Any]:
        """Handle OpenAI-specific errors.
        
        Args:
            error: The exception that was raised
            
        Returns:
            Standardized error response dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        error_dict = {
            "error": True,
            "error_type": error_type,
            "message": error_message,
            "provider": "openai"
        }
        
        # Add more specific error handling based on OpenAI error types
        if isinstance(error, RateLimitError):
            error_dict["retry_after"] = 60  # Default retry after 60 seconds
        
        return error_dict