from typing import Dict, List, Any, Optional, AsyncGenerator
import logging
import json
import asyncio
import cohere
from cohere.error import CohereAPIError, CohereConnectionError, CohereError

from .base import BaseProvider

logger = logging.getLogger(__name__)

class CohereProvider(BaseProvider):
    """Cohere API provider implementation."""
    
    def _setup_client(self) -> None:
        """Set up the Cohere API client."""
        self._client = cohere.Client(api_key=self.api_key)
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Retrieve available models from Cohere.
        
        Returns:
            A list of dictionaries containing model information
        """
        # Cohere doesn't have a list models endpoint, so we'll hardcode the available models
        # This list should be updated periodically or through configuration
        models = [
            {
                "id": "command",
                "name": "Command",
                "provider": "cohere",
                "created": None,
                "owned_by": "cohere"
            },
            {
                "id": "command-light",
                "name": "Command Light",
                "provider": "cohere",
                "created": None,
                "owned_by": "cohere"
            },
            {
                "id": "command-r",
                "name": "Command-R",
                "provider": "cohere",
                "created": None,
                "owned_by": "cohere"
            },
            {
                "id": "command-r-plus",
                "name": "Command-R Plus",
                "provider": "cohere",
                "created": None,
                "owned_by": "cohere"
            }
        ]
        
        return models
    
    def _convert_messages_to_cohere_format(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Convert standard message format to Cohere's chat format.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Cohere-formatted messages and preamble
        """
        cohere_messages = []
        preamble = None
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                preamble = content
            elif role == "user":
                cohere_messages.append({"role": "USER", "message": content})
            elif role == "assistant":
                cohere_messages.append({"role": "CHATBOT", "message": content})
        
        return cohere_messages, preamble
    
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
        """Generate a text completion from Cohere.
        
        Args:
            model: The model identifier to use
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter (alternative to temperature)
            stop_sequences: List of sequences where generation should stop
            presence_penalty: Penalty for token repetition (not supported by Cohere)
            frequency_penalty: Penalty for frequency of token repetition (not supported)
            additional_params: Additional provider-specific parameters
            
        Returns:
            A dictionary containing the completion response
        """
        try:
            # Convert messages to Cohere format
            cohere_messages, preamble = self._convert_messages_to_cohere_format(messages)
            
            params = {
                "model": model,
                "message": cohere_messages[-1]["message"] if cohere_messages else "",
                "chat_history": cohere_messages[:-1] if len(cohere_messages) > 1 else [],
                "temperature": temperature,
            }
            
            if preamble is not None:
                params["preamble"] = preamble
                
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if top_p is not None:
                params["p"] = top_p
            if stop_sequences is not None:
                params["stop_sequences"] = stop_sequences
            
            # Add any additional params provided
            if additional_params:
                params.update(additional_params)
            
            # Convert synchronous API to async
            response = await asyncio.to_thread(self._client.chat, **params)
            
            # Format the response in a standardized way
            result = {
                "id": response.generation_id if hasattr(response, "generation_id") else None,
                "model": model,
                "created": None,  # Cohere doesn't provide creation timestamp
                "provider": "cohere",
                "content": response.text,
                "role": "assistant",
                "finish_reason": None,  # Cohere doesn't provide finish reason
                "usage": {}
            }
            
            # Extract token usage if available
            if hasattr(response, "token_count") and response.token_count:
                result["usage"] = {
                    "prompt_tokens": response.token_count.get("prompt_tokens", None),
                    "completion_tokens": response.token_count.get("response_tokens", None),
                    "total_tokens": response.token_count.get("total_tokens", None)
                }
            
            return result
        
        except (CohereAPIError, CohereConnectionError, CohereError) as e:
            logger.error(f"Cohere API error: {str(e)}")
            return await self.handle_provider_error(e)
        except Exception as e:
            logger.error(f"Unexpected error with Cohere: {str(e)}")
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
        """Generate a streaming text completion from Cohere.
        
        Args:
            model: The model identifier to use
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter (alternative to temperature)
            stop_sequences: List of sequences where generation should stop
            presence_penalty: Penalty for token repetition (not supported by Cohere)
            frequency_penalty: Penalty for frequency of token repetition (not supported)
            additional_params: Additional provider-specific parameters
            
        Returns:
            An async generator yielding completion chunks
        """
        try:
            # Convert messages to Cohere format
            cohere_messages, preamble = self._convert_messages_to_cohere_format(messages)
            
            params = {
                "model": model,
                "message": cohere_messages[-1]["message"] if cohere_messages else "",
                "chat_history": cohere_messages[:-1] if len(cohere_messages) > 1 else [],
                "temperature": temperature,
                "stream": True,
            }
            
            if preamble is not None:
                params["preamble"] = preamble
                
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if top_p is not None:
                params["p"] = top_p
            if stop_sequences is not None:
                params["stop_sequences"] = stop_sequences
            
            # Add any additional params provided
            if additional_params:
                params.update(additional_params)
            
            # Convert synchronous API to async and handle streaming
            stream_response = await asyncio.to_thread(self._client.chat, **params)
            
            # Process stream responses
            async def process_stream():
                generation_id = None
                accumulated_text = ""
                
                for event in stream_response:
                    # Extract generation ID if available and not already set
                    if generation_id is None and hasattr(event, "generation_id"):
                        generation_id = event.generation_id
                    
                    # If text chunk is available
                    if hasattr(event, "text") and event.text is not None:
                        chunk_text = event.text
                        accumulated_text += chunk_text
                        
                        yield {
                            "id": generation_id,
                            "model": model,
                            "created": None,
                            "provider": "cohere",
                            "content": chunk_text,
                            "role": "assistant",
                            "finish_reason": None,
                            "is_chunk": True
                        }
                    
                    # If is_finished flag is present and true
                    if hasattr(event, "is_finished") and event.is_finished:
                        # Get token usage if available
                        usage = {}
                        if hasattr(event, "token_count") and event.token_count:
                            usage = {
                                "prompt_tokens": event.token_count.get("prompt_tokens", None),
                                "completion_tokens": event.token_count.get("response_tokens", None),
                                "total_tokens": event.token_count.get("total_tokens", None)
                            }
                        
                        yield {
                            "id": generation_id,
                            "model": model,
                            "created": None,
                            "provider": "cohere",
                            "content": "",  # Empty content for the final event
                            "role": "assistant",
                            "finish_reason": "stop",
                            "is_chunk": True,
                            "is_final": True,
                            "full_text": accumulated_text,
                            "usage": usage
                        }
            
            async for chunk in process_stream():
                yield chunk
        
        except (CohereAPIError, CohereConnectionError, CohereError) as e:
            logger.error(f"Cohere streaming API error: {str(e)}")
            yield await self.handle_provider_error(e)
        except Exception as e:
            logger.error(f"Unexpected error with Cohere streaming: {str(e)}")
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
            # Cohere provides a tokenize endpoint
            response = await asyncio.to_thread(self._client.tokenize, text=text)
            
            return {
                "token_count": len(response.tokens),
                "model": model,
                "provider": "cohere"
            }
        except Exception as e:
            logger.error(f"Error calculating tokens with Cohere: {str(e)}")
            return {
                "error": True,
                "error_type": type(e).__name__,
                "message": str(e),
                "provider": "cohere"
            }
    
    async def handle_provider_error(self, error: Exception) -> Dict[str, Any]:
        """Handle Cohere-specific errors.
        
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
            "provider": "cohere"
        }
        
        # Add more specific error handling for Cohere errors
        if isinstance(error, CohereAPIError) and "rate" in error_message.lower():
            error_dict["retry_after"] = 60  # Default retry after 60 seconds
        
        return error_dict