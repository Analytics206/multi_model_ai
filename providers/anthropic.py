from typing import Dict, List, Any, Optional, AsyncGenerator
import logging
import json
import asyncio
import anthropic
from anthropic import AsyncAnthropic, APIError, RateLimitError, APIConnectionError

from .base import BaseProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseProvider):
    """Anthropic API provider implementation."""
    
    def _setup_client(self) -> None:
        """Set up the Anthropic API client."""
        self._client = AsyncAnthropic(
            api_key=self.api_key
        )
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Retrieve available models from Anthropic.
        
        Returns:
            A list of dictionaries containing model information
        """
        # Anthropic doesn't have a list models endpoint, so we'll hardcode the available models
        # This list should be updated periodically or through configuration
        models = [
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "provider": "anthropic",
                "created": None,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "provider": "anthropic",
                "created": None,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "provider": "anthropic",
                "created": None,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-2.1",
                "name": "Claude 2.1",
                "provider": "anthropic",
                "created": None,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-2.0",
                "name": "Claude 2.0",
                "provider": "anthropic",
                "created": None,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-instant-1.2",
                "name": "Claude Instant 1.2",
                "provider": "anthropic",
                "created": None,
                "owned_by": "anthropic"
            }
        ]
        
        return models
    
    def _convert_messages_to_anthropic_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert standard message format to Anthropic's message format.
        
        Anthropic uses 'user' and 'assistant' roles instead of 'user' and 'assistant'.
        'system' messages need to be handled differently.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Anthropic-formatted messages
        """
        system_message = None
        anthropic_messages = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                system_message = content
            elif role == "user":
                anthropic_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                anthropic_messages.append({"role": "assistant", "content": content})
            # OpenAI has 'function' roles that we'll ignore for Anthropic
        
        return anthropic_messages, system_message
    
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
        """Generate a text completion from Anthropic.
        
        Args:
            model: The model identifier to use
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter (alternative to temperature)
            stop_sequences: List of sequences where generation should stop
            presence_penalty: Penalty for token repetition (not supported by Anthropic)
            frequency_penalty: Penalty for frequency of token repetition (not supported)
            additional_params: Additional provider-specific parameters
            
        Returns:
            A dictionary containing the completion response
        """
        try:
            # Convert messages to Anthropic format
            anthropic_messages, system_message = self._convert_messages_to_anthropic_format(messages)
            
            params = {
                "model": model,
                "messages": anthropic_messages,
                "temperature": temperature,
            }
            
            if system_message:
                params["system"] = system_message
                
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences is not None:
                params["stop_sequences"] = stop_sequences
            
            # Add any additional params provided
            if additional_params:
                params.update(additional_params)
            
            response = await self._client.messages.create(**params)
            
            # Format the response in a standardized way
            result = {
                "id": response.id,
                "model": response.model,
                "created": None,  # Anthropic doesn't provide creation timestamp
                "provider": "anthropic",
                "content": response.content[0].text,
                "role": "assistant",
                "finish_reason": response.stop_reason,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            return result
        
        except (APIError, RateLimitError, APIConnectionError) as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return await self.handle_provider_error(e)
        except Exception as e:
            logger.error(f"Unexpected error with Anthropic: {str(e)}")
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
        """Generate a streaming text completion from Anthropic.
        
        Args:
            model: The model identifier to use
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter (alternative to temperature)
            stop_sequences: List of sequences where generation should stop
            presence_penalty: Penalty for token repetition (not supported by Anthropic)
            frequency_penalty: Penalty for frequency of token repetition (not supported)
            additional_params: Additional provider-specific parameters
            
        Returns:
            An async generator yielding completion chunks
        """
        try:
            # Convert messages to Anthropic format
            anthropic_messages, system_message = self._convert_messages_to_anthropic_format(messages)
            
            params = {
                "model": model,
                "messages": anthropic_messages,
                "temperature": temperature,
                "stream": True,
            }
            
            if system_message:
                params["system"] = system_message
                
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences is not None:
                params["stop_sequences"] = stop_sequences
            
            # Add any additional params provided
            if additional_params:
                params.update(additional_params)
            
            stream = await self._client.messages.create(**params)
            
            async with stream as events:
                async for event in events:
                    if event.type == "content_block_delta":
                        yield {
                            "id": None,  # Will be available in the final event
                            "model": model,
                            "created": None,
                            "provider": "anthropic",
                            "content": event.delta.text,
                            "role": "assistant",
                            "finish_reason": None,  # Will be available in the final event
                            "is_chunk": True
                        }
                    elif event.type == "message_stop":
                        yield {
                            "id": event.message.id,
                            "model": model,
                            "created": None,
                            "provider": "anthropic",
                            "content": "",  # Empty content for the final event
                            "role": "assistant",
                            "finish_reason": event.message.stop_reason,
                            "is_chunk": True,
                            "is_final": True
                        }
        
        except (APIError, RateLimitError, APIConnectionError) as e:
            logger.error(f"Anthropic streaming API error: {str(e)}")
            yield await self.handle_provider_error(e)
        except Exception as e:
            logger.error(f"Unexpected error with Anthropic streaming: {str(e)}")
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
            # Use Anthropic's tokenizer
            token_count = anthropic.count_tokens(text)
            
            return {
                "token_count": token_count,
                "model": model,
                "provider": "anthropic"
            }
        except Exception as e:
            logger.error(f"Error calculating tokens with Anthropic: {str(e)}")
            return {
                "error": True,
                "error_type": type(e).__name__,
                "message": str(e),
                "provider": "anthropic"
            }
    
    async def handle_provider_error(self, error: Exception) -> Dict[str, Any]:
        """Handle Anthropic-specific errors.
        
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
            "provider": "anthropic"
        }
        
        # Add more specific error handling based on Anthropic error types
        if isinstance(error, RateLimitError):
            error_dict["retry_after"] = 60  # Default retry after 60 seconds
        
        return error_dict