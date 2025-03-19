from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
import logging

logger = logging.getLogger(__name__)

class BaseProvider(ABC):
    """Abstract base class for AI providers integration.
    
    All provider implementations must inherit from this class and implement
    its abstract methods to ensure a consistent interface.
    """
    
    def __init__(self, api_key: str, organization_id: Optional[str] = None):
        """Initialize the provider with authentication credentials.
        
        Args:
            api_key: The API key for authentication with the provider
            organization_id: Optional organization ID for providers that support it
        """
        self.api_key = api_key
        self.organization_id = organization_id
        self._client = None
        self._setup_client()
    
    @abstractmethod
    def _setup_client(self) -> None:
        """Set up the API client for the provider.
        
        This method should initialize the provider-specific client library
        and set it to self._client.
        """
        pass
    
    @abstractmethod
    async def get_models(self) -> List[Dict[str, Any]]:
        """Retrieve available models from the provider.
        
        Returns:
            A list of dictionaries containing model information
        """
        pass
    
    @abstractmethod
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
        """Generate a text completion from the model.
        
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
        pass
    
    @abstractmethod
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
        """Generate a streaming text completion from the model.
        
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
        pass
    
    @abstractmethod
    async def calculate_tokens(
        self, 
        text: str, 
        model: str
    ) -> Dict[str, int]:
        """Calculate the number of tokens in the provided text.
        
        Args:
            text: The text to tokenize
            model: The model to use for tokenization
            
        Returns:
            Dictionary with token count information
        """
        pass
    
    async def handle_provider_error(self, error: Exception) -> Dict[str, Any]:
        """Handle provider-specific errors and return standardized error response.
        
        Args:
            error: The exception that was raised
            
        Returns:
            Standardized error response dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        logger.error(f"Provider error: {error_type} - {error_message}")
        
        return {
            "error": True,
            "error_type": error_type,
            "message": error_message,
            "provider": self.__class__.__name__
        }
    
    def __repr__(self) -> str:
        """Return string representation of the provider instance."""
        return f"{self.__class__.__name__}(organization_id={self.organization_id})"