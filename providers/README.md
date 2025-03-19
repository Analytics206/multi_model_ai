# AI Provider API Integration

This module implements integrations with various AI model providers, offering a unified interface for model interactions.

## Supported Providers

- **OpenAI**: GPT models (GPT-3.5, GPT-4, etc.)
- **Anthropic**: Claude models (Claude 3 Opus, Sonnet, Haiku, etc.)
- **Google**: Gemini models
- **Cohere**: Command models

## Architecture

The provider module is designed with the following components:

1. **Base Provider (`BaseProvider`)**: Abstract base class that defines the common interface all providers must implement.
2. **Provider Implementations**: Provider-specific implementations of the base provider interface.
3. **Provider Factory (`ProviderFactory`)**: Manages provider instances and provides utility methods for working with providers.

## Usage Examples

### Basic Usage

```python
import asyncio
from providers import factory

async def main():
    # Get a provider instance
    openai_provider = await factory.get_provider(
        provider_name="openai",
        api_key="your_api_key"
    )
    
    # Generate a completion
    response = await openai_provider.generate_completion(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ],
        max_tokens=100,
        temperature=0.7
    )
    
    print(response["content"])

asyncio.run(main())
```

### Using the Factory for Simplified API Access

```python
import asyncio
from providers import factory

async def main():
    # Generate a completion using the factory
    response = await factory.generate_completion(
        provider_name="anthropic",
        model="claude-3-opus-20240229",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain quantum computing in simple terms."}
        ],
        api_key="your_api_key",
        max_tokens=500,
        temperature=0.7
    )
    
    print(response["content"])

asyncio.run(main())
```

### Streaming Responses

```python
import asyncio
from providers import factory

async def main():
    # Generate a streaming completion
    stream = await factory.generate_completion(
        provider_name="openai",
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a poem about AI."}
        ],
        api_key="your_api_key",
        temperature=0.7,
        stream=True
    )
    
    # Process the stream
    async for chunk in stream:
        if not chunk.get("error", False):
            print(chunk["content"], end="", flush=True)

asyncio.run(main())
```

### Rate Limit Handling

```python
import asyncio
from providers import factory

async def main():
    # Define the coroutine
    coro = factory.generate_completion(
        provider_name="openai",
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Explain the theory of relativity."}
        ],
        api_key="your_api_key"
    )
    
    # Execute with rate limit handling
    response = await factory.run_with_rate_limit_handling(
        coro,
        max_retries=5,
        base_delay=2.0
    )
    
    print(response["content"])

asyncio.run(main())
```

## Key Features

- **Unified Interface**: Consistent API across different providers
- **Asynchronous Support**: All operations are async for optimal performance
- **Streaming Support**: Stream completions for real-time responses
- **Token Calculation**: Calculate token usage for prompt engineering
- **Rate Limit Handling**: Automatic retry with exponential backoff for rate limit errors
- **Provider Auto-Detection**: Automatically determine the provider for a given model

## Extending

To add a new provider:

1. Create a new provider class that inherits from `BaseProvider`
2. Implement all abstract methods
3. Add the provider to the `PROVIDER_REGISTRY` in `__init__.py`

## Dependencies

Each provider requires its corresponding Python SDK:
- OpenAI: `openai`
- Anthropic: `anthropic`
- Google: `google-generativeai`
- Cohere: `cohere`