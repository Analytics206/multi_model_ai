from typing import Dict, List, Any, Optional, AsyncGenerator
import logging
import asyncio
import anthropic

from .base import BaseProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseProvider):
    """Anthropic API provider implementation."""
    
    def _setup_client(self) -> None:
        """Set up the Anthropic API client."""
        self._client = anthropic.AsyncAnthropic(
            api_key=self.api_key
        )
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Retrieve available models from Anthropic."""
        # Anthropic doesn't have a list models endpoint, so we'll hardcode the available models
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
            }
        ]
        
        return models
    
    def _convert_messages_to_anthropic_format(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert standard message format to Anthropic's message format."""
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
        """Generate a text completion from Anthropic."""
        try:
            # Convert messages to Anthropic format
            anthropic_messages, system_message = self._convert_messages_to_anthropic_format(messages)
            
            # Anthropic requires max_tokens
            if max_tokens is None:
                max_tokens = 1024
            
            params = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            if system_message:
                params["system"] = system_message
                
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences is not None:
                params["stop_sequences"] = stop_sequences
            
            # Add any additional params provided
            if additional_params:
                params.update(additional_params)
            
            # Debug the params
            logger.debug(f"Anthropic API parameters: {params}")
            
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
        
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
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
        """Generate a streaming text completion from Anthropic."""
        try:
            # Convert messages to Anthropic format
            anthropic_messages, system_message = self._convert_messages_to_anthropic_format(messages)
            
            # Anthropic requires max_tokens
            if max_tokens is None:
                max_tokens = 1024
            
            params = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            }
            
            if system_message:
                params["system"] = system_message
                
            if top_p is not None:
                params["top_p"] = top_p
            if stop_sequences is not None:
                params["stop_sequences"] = stop_sequences
            
            # Add any additional params provided
            if additional_params:
                params.update(additional_params)
            
            # Debug the params
            logger.debug(f"Anthropic streaming API parameters: {params}")
            
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
        
        except Exception as e:
            logger.error(f"Anthropic streaming API error: {str(e)}")
            yield await self.handle_provider_error(e)
    
    async def calculate_tokens(self, text: str, model: str) -> Dict[str, int]:
        """Calculate the number of tokens in the provided text."""
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