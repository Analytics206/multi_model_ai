from typing import Dict, List, Any, Optional, AsyncGenerator
import logging
import json
import asyncio
import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, GoogleAPIError

from .base import BaseProvider

logger = logging.getLogger(__name__)

class GoogleProvider(BaseProvider):
    """Google Gemini API provider implementation."""
    
    def _setup_client(self) -> None:
        """Set up the Google Gemini API client."""
        genai.configure(api_key=self.api_key)
        self._client = genai
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Retrieve available models from Google Gemini.
        
        Returns:
            A list of dictionaries containing model information
        """
        try:
            # Convert the synchronous API to async
            models_list = await asyncio.to_thread(self._client.list_models)
            
            models = []
            for model in models_list:
                # Only include text generation models
                if not hasattr(model, "supported_generation_methods") or not model.supported_generation_methods:
                    continue
                
                if "generateContent" in model.supported_generation_methods:
                    models.append({
                        "id": model.name,
                        "name": model.display_name or model.name,
                        "provider": "google",
                        "created": None,  # Google doesn't provide creation timestamp
                        "owned_by": "google",
                        "description": model.description if hasattr(model, "description") else None,
                        "version": model.version if hasattr(model, "version") else None
                    })
            
            return models
        except Exception as e:
            logger.error(f"Error fetching Google Gemini models: {str(e)}")
            return await self.handle_provider_error(e)
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]):
        """Convert standard message format to Google Gemini's content format.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Gemini-formatted content
        """
        gemini_content = []
        system_message = None
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                system_message = content
            elif role == "user":
                gemini_content.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                gemini_content.append({"role": "model", "parts": [{"text": content}]})
        
        return gemini_content, system_message
    
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
        """Generate a text completion from Google Gemini.
        
        Args:
            model: The model identifier to use
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter (alternative to temperature)
            stop_sequences: List of sequences where generation should stop
            presence_penalty: Penalty for token repetition (not supported by Gemini)
            frequency_penalty: Penalty for frequency of token repetition (not supported)
            additional_params: Additional provider-specific parameters
            
        Returns:
            A dictionary containing the completion response
        """
        try:
            # Convert messages to Gemini format
            gemini_content, system_message = self._convert_messages_to_gemini_format(messages)
            
            # Get the model
            model_instance = await asyncio.to_thread(self._client.GenerativeModel, model_name=model)
            
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
            }
            
            if max_tokens is not None:
                generation_config["max_output_tokens"] = max_tokens
            if top_p is not None:
                generation_config["top_p"] = top_p
            if stop_sequences is not None:
                generation_config["stop_sequences"] = stop_sequences
                
            # Set generation config
            model_instance.generation_config = generation_config
            
            # Include system message if provided
            if system_message:
                # Google's API has no direct system message, so we prepend it to the first user message
                if gemini_content and gemini_content[0]["role"] == "user":
                    first_user_msg = gemini_content[0]["parts"][0]["text"]
                    gemini_content[0]["parts"][0]["text"] = f"[SYSTEM: {system_message}]\n\n{first_user_msg}"
            
            # Call the API
            response = await asyncio.to_thread(
                model_instance.generate_content,
                contents=gemini_content
            )
            
            # Format the response in a standardized way
            result = {
                "id": None,  # Gemini doesn't provide a response ID
                "model": model,
                "created": None,  # Gemini doesn't provide creation timestamp
                "provider": "google",
                "content": response.text,
                "role": "assistant",
                "finish_reason": None,  # Gemini doesn't provide finish reason
                "usage": {
                    "prompt_tokens": None,  # Gemini doesn't provide token usage
                    "completion_tokens": None,
                    "total_tokens": None
                }
            }
            
            # Try to get usage information if available
            if hasattr(response, "usage_metadata"):
                result["usage"] = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", None),
                    "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", None),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", None)
                }
            
            return result
        
        except (ResourceExhausted, ServiceUnavailable, GoogleAPIError) as e:
            logger.error(f"Google Gemini API error: {str(e)}")
            return await self.handle_provider_error(e)
        except Exception as e:
            logger.error(f"Unexpected error with Google Gemini: {str(e)}")
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
        """Generate a streaming text completion from Google Gemini.
        
        Args:
            model: The model identifier to use
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter (alternative to temperature)
            stop_sequences: List of sequences where generation should stop
            presence_penalty: Penalty for token repetition (not supported by Gemini)
            frequency_penalty: Penalty for frequency of token repetition (not supported)
            additional_params: Additional provider-specific parameters
            
        Returns:
            An async generator yielding completion chunks
        """
        try:
            # Convert messages to Gemini format
            gemini_content, system_message = self._convert_messages_to_gemini_format(messages)
            
            # Get the model
            model_instance = await asyncio.to_thread(self._client.GenerativeModel, model_name=model)
            
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
            }
            
            if max_tokens is not None:
                generation_config["max_output_tokens"] = max_tokens
            if top_p is not None:
                generation_config["top_p"] = top_p
            if stop_sequences is not None:
                generation_config["stop_sequences"] = stop_sequences
                
            # Set generation config
            model_instance.generation_config = generation_config
            
            # Include system message if provided
            if system_message:
                # Google's API has no direct system message, so we prepend it to the first user message
                if gemini_content and gemini_content[0]["role"] == "user":
                    first_user_msg = gemini_content[0]["parts"][0]["text"]
                    gemini_content[0]["parts"][0]["text"] = f"[SYSTEM: {system_message}]\n\n{first_user_msg}"
            
            # Call the API with streaming
            response_stream = await asyncio.to_thread(
                model_instance.generate_content,
                contents=gemini_content,
                stream=True
            )
            
            # Process the stream
            async def process_stream():
                try:
                    accumulated_text = ""
                    async for chunk in asyncio.as_completed([asyncio.to_thread(lambda: list(response_stream))]):
                        for item in await chunk:
                            if hasattr(item, "text"):
                                chunk_text = item.text or ""
                                accumulated_text += chunk_text
                                
                                yield {
                                    "id": None,
                                    "model": model,
                                    "created": None,
                                    "provider": "google",
                                    "content": chunk_text,
                                    "role": "assistant",
                                    "finish_reason": None,
                                    "is_chunk": True
                                }
                    
                    # Final chunk with complete text
                    yield {
                        "id": None,
                        "model": model,
                        "created": None,
                        "provider": "google",
                        "content": "",  # Empty for final chunk
                        "role": "assistant",
                        "finish_reason": "stop",
                        "is_chunk": True,
                        "is_final": True,
                        "full_text": accumulated_text
                    }
                except Exception as e:
                    yield await self.handle_provider_error(e)
            
            async for chunk in process_stream():
                yield chunk
        
        except (ResourceExhausted, ServiceUnavailable, GoogleAPIError) as e:
            logger.error(f"Google Gemini streaming API error: {str(e)}")
            yield await self.handle_provider_error(e)
        except Exception as e:
            logger.error(f"Unexpected error with Google Gemini streaming: {str(e)}")
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
            # Google doesn't provide a proper tokenizer in their API
            # We can make a rough estimate based on the standard ratio of 4 chars per token
            # This is just an approximation and not accurate
            char_count = len(text)
            estimated_tokens = round(char_count / 4)
            
            return {
                "token_count": estimated_tokens,
                "model": model,
                "provider": "google",
                "is_estimate": True
            }
        except Exception as e:
            logger.error(f"Error calculating tokens for Google Gemini: {str(e)}")
            return {
                "error": True,
                "error_type": type(e).__name__,
                "message": str(e),
                "provider": "google"
            }
    
    async def handle_provider_error(self, error: Exception) -> Dict[str, Any]:
        """Handle Google Gemini-specific errors.
        
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
            "provider": "google"
        }
        
        # Add more specific error handling based on Google error types
        if isinstance(error, ResourceExhausted):
            error_dict["retry_after"] = 60  # Default retry after 60 seconds
        
        return error_dict